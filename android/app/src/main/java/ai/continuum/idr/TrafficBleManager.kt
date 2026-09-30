package ai.continuum.idr

import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager
import android.bluetooth.le.AdvertiseCallback
import android.bluetooth.le.AdvertiseData
import android.bluetooth.le.AdvertiseSettings
import android.bluetooth.le.BluetoothLeAdvertiser
import android.bluetooth.le.BluetoothLeScanner
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanFilter
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.Context
import android.os.ParcelUuid
import android.util.Log
import java.nio.ByteBuffer
import java.util.UUID

data class TrafficHazardReport(
    val hazardType: String,
    val severity: Double,
    val latitude: Double,
    val longitude: Double,
    val timestampMs: Long,
    val vehicleId: String
)

/**
 * Handles localized Vehicle-to-Vehicle (V2V) cooperative hazard sharing
 * over Bluetooth Low Energy (BLE) without cellular dependency.
 */
class TrafficBleManager(private val context: Context) {

    interface TrafficReportListener {
        fun onHazardReceived(report: TrafficHazardReport)
    }

    private var listener: TrafficReportListener? = null
    private val bluetoothManager = context.getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager
    private val adapter: BluetoothAdapter? = bluetoothManager?.adapter
    private var advertiser: BluetoothLeAdvertiser? = null
    private var scanner: BluetoothLeScanner? = null
    private var isAdvertising = false
    private var isScanning = false

    private val SERVICE_UUID = UUID.fromString("0000C1D0-0000-1000-8000-00805F9B34FB")
    private val CONTINUUM_MANUFACTURER_ID = 0x0C1D // "CID"

    private val advertiseCallback = object : AdvertiseCallback() {
        override fun onStartSuccess(settingsInEffect: AdvertiseSettings?) {
            isAdvertising = true
            Log.i("TrafficBle", "BLE advertising started successfully")
        }

        override fun onStartFailure(errorCode: Int) {
            isAdvertising = false
            Log.w("TrafficBle", "BLE advertising failed with code $errorCode")
        }
    }

    private val scanCallback = object : ScanCallback() {
        override fun onScanResult(callbackType: Int, result: ScanResult?) {
            result?.scanRecord?.let { record ->
                val data = record.getManufacturerSpecificData(CONTINUUM_MANUFACTURER_ID)
                if (data != null && data.size >= 18) {
                    parseHazardPayload(data)?.let { listener?.onHazardReceived(it) }
                }
            }
        }
    }

    fun start(listener: TrafficReportListener) {
        this.listener = listener
        if (adapter == null || !adapter.isEnabled) {
            Log.w("TrafficBle", "Bluetooth adapter not enabled or unavailable")
            return
        }

        try {
            advertiser = adapter.bluetoothLeAdvertiser
            scanner = adapter.bluetoothLeScanner
            startScanning()
        } catch (e: SecurityException) {
            Log.w("TrafficBle", "Missing Bluetooth permissions: ${e.message}")
        }
    }

    fun stop() {
        stopAdvertising()
        stopScanning()
        listener = null
    }

    private fun startScanning() {
        if (isScanning || scanner == null) return
        try {
            val filter = ScanFilter.Builder()
                .setManufacturerData(CONTINUUM_MANUFACTURER_ID, byteArrayOf())
                .build()
            val settings = ScanSettings.Builder()
                .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
                .build()
            scanner?.startScan(listOf(filter), settings, scanCallback)
            isScanning = true
        } catch (e: SecurityException) {
            Log.w("TrafficBle", "Scan permission missing: ${e.message}")
        } catch (e: Exception) {
            Log.w("TrafficBle", "Failed to start BLE scan: ${e.message}")
        }
    }

    private fun stopScanning() {
        if (!isScanning) return
        try {
            scanner?.stopScan(scanCallback)
        } catch (e: Exception) {
            // Ignore
        }
        isScanning = false
    }

    fun broadcastHazard(hazardType: String, severity: Double, lat: Double, lon: Double) {
        if (advertiser == null) return
        val typeByte: Byte = when (hazardType) {
            "GNSS_OUTAGE" -> 1
            "SPEED_BREAKER" -> 2
            "POTHOLE" -> 3
            "TRAFFIC_JAM" -> 4
            else -> 0
        }

        val buf = ByteBuffer.allocate(18)
        buf.put(typeByte)
        buf.put((severity.coerceIn(0.0, 1.0) * 100.0).toInt().toByte())
        buf.putDouble(lat)
        buf.putDouble(lon)

        val settings = AdvertiseSettings.Builder()
            .setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY)
            .setTxPowerLevel(AdvertiseSettings.ADVERTISE_TX_POWER_HIGH)
            .setConnectable(false)
            .setTimeout(3000) // 3 seconds beacon burst
            .build()

        val data = AdvertiseData.Builder()
            .addManufacturerData(CONTINUUM_MANUFACTURER_ID, buf.array())
            .setIncludeDeviceName(false)
            .build()

        try {
            if (isAdvertising) advertiser?.stopAdvertising(advertiseCallback)
            advertiser?.startAdvertising(settings, data, advertiseCallback)
        } catch (e: SecurityException) {
            Log.w("TrafficBle", "Advertise permission missing: ${e.message}")
        } catch (e: Exception) {
            Log.w("TrafficBle", "Failed to broadcast hazard: ${e.message}")
        }
    }

    private fun stopAdvertising() {
        if (!isAdvertising) return
        try {
            advertiser?.stopAdvertising(advertiseCallback)
        } catch (e: Exception) {
            // Ignore
        }
        isAdvertising = false
    }

    private fun parseHazardPayload(bytes: ByteArray): TrafficHazardReport? {
        try {
            val buf = ByteBuffer.wrap(bytes)
            val typeByte = buf.get().toInt()
            val hazard = when (typeByte) {
                1 -> "GNSS_OUTAGE"
                2 -> "SPEED_BREAKER"
                3 -> "POTHOLE"
                4 -> "TRAFFIC_JAM"
                else -> "UNKNOWN"
            }
            val sev = (buf.get().toInt() and 0xFF) / 100.0
            val lat = buf.getDouble()
            val lon = buf.getDouble()

            return TrafficHazardReport(
                hazardType = hazard,
                severity = sev,
                latitude = lat,
                longitude = lon,
                timestampMs = System.currentTimeMillis(),
                vehicleId = "peer_ble"
            )
        } catch (e: Exception) {
            return null
        }
    }
}
