package ai.continuum.idr

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.location.Location
import android.os.Build
import android.os.IBinder
import java.io.BufferedWriter
import java.io.File
import java.io.FileWriter
import java.security.MessageDigest
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/** Foreground trip recorder. Each line is an independently recoverable JSON event. */
class TrackingService : Service(),
    ContinuumLocationEngine.LocationUpdateCallback,
    TrafficBleManager.TrafficReportListener {

    private var engine: ContinuumLocationEngine? = null
    private var bleManager: TrafficBleManager? = null
    private var writer: BufferedWriter? = null
    private var eventCount = 0
    private var currentProfile = ContinuumLocationEngine.VehicleProfile.CAR

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startForeground(NOTIFICATION_ID, notification())
        if (engine != null) return START_STICKY

        val profileStr = intent?.getStringExtra(EXTRA_PROFILE) ?: "CAR"
        currentProfile = try {
            ContinuumLocationEngine.VehicleProfile.valueOf(profileStr)
        } catch (e: Exception) {
            ContinuumLocationEngine.VehicleProfile.CAR
        }

        val stamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(Date())
        val directory = File(getExternalFilesDir(null), "trips").apply { mkdirs() }
        val tripFile = File(directory, "continuum_$stamp.jsonl")
        writer = BufferedWriter(FileWriter(tripFile, true))

        try {
            val modelBytes = assets.open("motion_portable.json").use { it.readBytes() }
            val modelJson = String(modelBytes, Charsets.UTF_8)
            val modelHash = computeSha256(modelBytes)

            // Optional road pack loading
            val roadPack = try {
                assets.open("sample_road_pack.json").use { RoadGraphPack.fromInputStream(it) }
            } catch (e: Exception) {
                null
            }

            val runner = PortableTreeRunner.fromJsonString(modelJson)
            engine = ContinuumLocationEngine(
                context = this,
                portableRunner = runner,
                vehicleProfile = currentProfile,
                roadGraphPack = roadPack
            ).also { it.start(this) }

            // Write Line 1 Metadata Header (Schema 1.0.0)
            write(
                "metadata",
                "version" to "1.0.0",
                "model_hash" to modelHash,
                "device_model" to Build.MODEL,
                "device_manufacturer" to Build.MANUFACTURER,
                "os_version" to Build.VERSION.RELEASE,
                "vehicle_profile" to currentProfile.name,
                "start_time_ms" to System.currentTimeMillis()
            )
            writer?.flush()

            // Initialize BLE Cooperative Traffic Manager
            bleManager = TrafficBleManager(this).also { it.start(this) }

            status("Recording sensors and GNSS. File: continuum_$stamp.jsonl")
        } catch (error: Exception) {
            status("Could not start recorder: ${error.message}")
            stopSelf()
        }
        return START_STICKY
    }

    override fun onDestroy() {
        engine?.stop()
        bleManager?.stop()
        writer?.close()
        engine = null
        bleManager = null
        writer = null
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onLocationUpdate(
        location: Location,
        isFallback: Boolean,
        state: ContinuumLocationEngine.FallbackState
    ) {
        onLocationUpdate(location, isFallback, state, engine?.latestMatchResult)
    }

    override fun onLocationUpdate(
        location: Location,
        isFallback: Boolean,
        state: ContinuumLocationEngine.FallbackState,
        matchResult: MapMatchResult?
    ) {
        write(
            "position",
            "lat" to location.latitude,
            "lon" to location.longitude,
            "speed_mps" to location.speed,
            "bearing_deg" to location.bearing,
            "accuracy_m" to location.accuracy,
            "fallback" to isFallback,
            "state" to state.name,
            "matched_segment" to matchResult?.segmentId,
            "match_confidence" to (matchResult?.matchConfidence ?: 0.0),
            "is_ambiguous" to (matchResult?.isAmbiguous ?: false),
            "lean_angle_deg" to (engine?.currentLeanAngleDeg ?: 0.0)
        )
        status("${state.name}: %.1f m accuracy, %.1f m/s".format(location.accuracy, location.speed))

        // Broadcast detailed telemetry to MainActivity
        sendBroadcast(
            Intent(ACTION_TELEMETRY).setPackage(packageName).apply {
                putExtra("lat", location.latitude)
                putExtra("lon", location.longitude)
                putExtra("speed_mps", location.speed)
                putExtra("bearing_deg", location.bearing)
                putExtra("accuracy_m", location.accuracy)
                putExtra("is_fallback", isFallback)
                putExtra("state", state.name)
                putExtra("segment_id", matchResult?.segmentId)
                putExtra("match_confidence", matchResult?.matchConfidence ?: 0.0)
                putExtra("lean_angle_deg", engine?.currentLeanAngleDeg ?: 0.0)
            }
        )
    }

    override fun onRawGnss(location: Location) {
        write(
            "gnss",
            "lat" to location.latitude,
            "lon" to location.longitude,
            "speed_mps" to location.speed,
            "bearing_deg" to location.bearing,
            "accuracy_m" to location.accuracy,
            "provider" to (location.provider ?: "gps")
        )
    }

    override fun onRawImu(sensorType: Int, timestampNs: Long, values: FloatArray) {
        write(
            "imu",
            "sensor_type" to sensorType,
            "timestamp_ns" to timestampNs,
            "values" to JsonRaw(values.joinToString(prefix = "[", postfix = "]"))
        )
    }

    override fun onSurfaceAnomaly(eventType: String, severity: Double) {
        write("surface", "kind" to eventType, "severity" to severity)
        status("Anomaly detected: $eventType (severity %.2f)".format(severity))

        // Broadcast locally to peers via BLE
        engine?.let { eng ->
            bleManager?.broadcastHazard(
                hazardType = eventType,
                severity = severity,
                lat = eng.currentLat,
                lon = eng.currentLon
            )
        }
    }

    override fun onMountShiftDetected() {
        write("mount", "event" to "tilt_shift_detected")
        status("Mount alignment changed; reposition the phone")
    }

    override fun onHazardReceived(report: TrafficHazardReport) {
        write(
            "traffic",
            "hazard" to report.hazardType,
            "severity" to report.severity,
            "peer_lat" to report.latitude,
            "peer_lon" to report.longitude,
            "vehicle_id" to report.vehicleId
        )
        status("BLE Traffic Alert: ${report.hazardType} ahead!")
    }

    private fun write(type: String, vararg fields: Pair<String, Any?>) {
        val payload = fields.joinToString(",") { (key, value) -> "\"$key\":${jsonValue(value)}" }
        writer?.append("{\"type\":\"$type\",\"wall_time_ms\":${System.currentTimeMillis()},$payload}\n")
        eventCount += 1
        if (eventCount % 100 == 0) writer?.flush()
    }

    private fun jsonValue(value: Any?): String = when (value) {
        null -> "null"
        is JsonRaw -> value.value
        is String -> "\"${value.replace("\\", "\\\\").replace("\"", "\\\"")}\""
        else -> value.toString()
    }

    private data class JsonRaw(val value: String)

    private fun status(value: String) {
        sendBroadcast(Intent(ACTION_STATUS).setPackage(packageName).putExtra(EXTRA_STATUS, value))
    }

    private fun computeSha256(bytes: ByteArray): String {
        val md = MessageDigest.getInstance("SHA-256")
        val digest = md.digest(bytes)
        return digest.joinToString("") { "%02x".format(it) }
    }

    private fun notification(): Notification {
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(
            NotificationChannel(
                CHANNEL_ID,
                "Continuum trip recording",
                NotificationManager.IMPORTANCE_LOW
            )
        )
        val openApp = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE
        )
        return Notification.Builder(this, CHANNEL_ID)
            .setContentTitle("Continuum IDR recording")
            .setContentText("Capturing phone sensors, GNSS, and road topology")
            .setSmallIcon(android.R.drawable.ic_menu_mylocation)
            .setContentIntent(openApp)
            .setOngoing(true)
            .build()
    }

    companion object {
        const val ACTION_STATUS = "ai.continuum.idr.STATUS"
        const val ACTION_TELEMETRY = "ai.continuum.idr.TELEMETRY"
        const val EXTRA_STATUS = "status"
        const val EXTRA_PROFILE = "profile"
        private const val CHANNEL_ID = "continuum_recording"
        private const val NOTIFICATION_ID = 2041
    }
}
