package ai.continuum.idr

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.location.Location
import android.os.IBinder
import java.io.BufferedWriter
import java.io.File
import java.io.FileWriter
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/** Foreground trip recorder. Each line is an independently recoverable JSON event. */
class TrackingService : Service(), ContinuumLocationEngine.LocationUpdateCallback {
    private var engine: ContinuumLocationEngine? = null
    private var writer: BufferedWriter? = null
    private var eventCount = 0

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startForeground(NOTIFICATION_ID, notification())
        if (engine != null) return START_STICKY
        val stamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(Date())
        val directory = File(getExternalFilesDir(null), "trips").apply { mkdirs() }
        writer = BufferedWriter(FileWriter(File(directory, "continuum_$stamp.jsonl"), true))
        try {
            val modelJson = assets.open("motion_portable.json").bufferedReader().use { it.readText() }
            engine = ContinuumLocationEngine(this, PortableTreeRunner.fromJsonString(modelJson)).also { it.start(this) }
            status("Recording sensors and GNSS. File: continuum_$stamp.jsonl")
        } catch (error: Exception) {
            status("Could not start recorder: ${error.message}")
            stopSelf()
        }
        return START_STICKY
    }

    override fun onDestroy() {
        engine?.stop()
        writer?.close()
        engine = null
        writer = null
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onLocationUpdate(location: Location, isFallback: Boolean, state: ContinuumLocationEngine.FallbackState) {
        write("position", "lat" to location.latitude, "lon" to location.longitude, "speed_mps" to location.speed, "bearing_deg" to location.bearing, "accuracy_m" to location.accuracy, "fallback" to isFallback, "state" to state.name)
        status("${state.name}: %.1f m accuracy, %.1f m/s".format(location.accuracy, location.speed))
    }

    override fun onRawGnss(location: Location) {
        write("gnss", "lat" to location.latitude, "lon" to location.longitude, "speed_mps" to location.speed, "bearing_deg" to location.bearing, "accuracy_m" to location.accuracy, "provider" to (location.provider ?: "gps"))
    }

    override fun onRawImu(sensorType: Int, timestampNs: Long, values: FloatArray) {
        write("imu", "sensor_type" to sensorType, "timestamp_ns" to timestampNs, "values" to JsonRaw(values.joinToString(prefix = "[", postfix = "]")))
    }

    override fun onSurfaceAnomaly(eventType: String, severity: Double) {
        write("surface", "kind" to eventType, "severity" to severity)
    }

    override fun onMountShiftDetected() { status("Mount alignment changed; reposition the phone") }

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

    private fun notification(): Notification {
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(NotificationChannel(CHANNEL_ID, "Continuum trip recording", NotificationManager.IMPORTANCE_LOW))
        val openApp = PendingIntent.getActivity(this, 0, Intent(this, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE)
        return Notification.Builder(this, CHANNEL_ID).setContentTitle("Continuum IDR recording")
            .setContentText("Capturing phone sensors and GNSS").setSmallIcon(android.R.drawable.ic_menu_mylocation)
            .setContentIntent(openApp).setOngoing(true).build()
    }

    companion object {
        const val ACTION_STATUS = "ai.continuum.idr.STATUS"
        const val EXTRA_STATUS = "status"
        private const val CHANNEL_ID = "continuum_recording"
        private const val NOTIFICATION_ID = 2041
    }
}
