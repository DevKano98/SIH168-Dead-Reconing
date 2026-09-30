package ai.continuum.idr

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Bundle
import android.os.SystemClock
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Drop-in Android location fallback engine.
 * Transparently wraps Android GPS and IMU sensors to provide uninterrupted
 * location updates even inside tunnels, parking garages, and urban canyons.
 * Compatible with Google Maps SDK, Mapbox Navigation SDK, and OSMDroid.
 */
class ContinuumLocationEngine(
    private val context: Context,
    private val portableRunner: PortableTreeRunner
) : LocationListener, SensorEventListener {

    enum class FallbackState {
        GNSS_HEALTHY,
        OUTAGE_PENDING,
        FALLBACK_ACTIVE,
        RECOVERING
    }

    interface LocationUpdateCallback {
        fun onLocationUpdate(location: Location, isFallback: Boolean, state: FallbackState)
        fun onSurfaceAnomaly(eventType: String, severity: Double)
        fun onMountShiftDetected()
        fun onRawGnss(location: Location)
        fun onRawImu(sensorType: Int, timestampNs: Long, values: FloatArray)
    }

    private val locationManager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
    private val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager

    private var callback: LocationUpdateCallback? = null
    private var isTracking = false

    // Timing & Fallback thresholds
    private val GNSS_TIMEOUT_MS = 2000L
    private val GNSS_ACCURACY_THRESHOLD_M = 25.0f
    private var lastFixElapsedRealtimeMs = 0L

    // Current State
    var currentState = FallbackState.GNSS_HEALTHY
        private set

    private var currentLat = 0.0
    private var currentLon = 0.0
    private var currentSpeedMps = 0.0f
    private var currentBearingDeg = 0.0f
    private var currentUncertaintyM = 5.0f
    private var hasNavigationOrigin = false

    // IMU buffer for 2.0s causal feature calculation (20 samples at 10 Hz)
    private val imuWindow = ArrayDeque<DoubleArray>(20)
    private var lastImuTimestampNs = 0L
    private var lastFeatureSampleTimestampNs = 0L
    private val latestLinearAcceleration = DoubleArray(3)
    private val latestGravity = DoubleArray(3) { if (it == 2) 9.80665 else 0.0 }
    private var hasLinearAccelerationSensor = false

    // Mount change detection (gravity tracking)
    private var refGravityX = 0f
    private var refGravityY = 0f
    private var refGravityZ = 9.81f
    private var isRefGravitySet = false

    fun start(updateCallback: LocationUpdateCallback) {
        if (isTracking) return
        this.callback = updateCallback
        this.isTracking = true

        // 1. Register GNSS Provider
        try {
            locationManager.requestLocationUpdates(
                LocationManager.GPS_PROVIDER,
                1000L,
                0f,
                this
            )
        } catch (e: SecurityException) {
            // Require ACCESS_FINE_LOCATION
        }

        // 2. Register IMU Sensors (Accelerate & Gyroscope at SENSOR_DELAY_GAME ~50 Hz or SENSOR_DELAY_UI ~16 Hz)
        val linearAccel = sensorManager.getDefaultSensor(Sensor.TYPE_LINEAR_ACCELERATION)
        val accel = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        val gyro = sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE)
        val gravity = sensorManager.getDefaultSensor(Sensor.TYPE_GRAVITY)

        hasLinearAccelerationSensor = linearAccel != null
        (linearAccel ?: accel)?.let { sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_GAME) }
        gyro?.let { sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_GAME) }
        gravity?.let { sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_GAME) }
    }

    fun stop() {
        if (!isTracking) return
        isTracking = false
        locationManager.removeUpdates(this)
        sensorManager.unregisterListener(this)
        imuWindow.clear()
    }

    override fun onLocationChanged(location: Location) {
        lastFixElapsedRealtimeMs = SystemClock.elapsedRealtime()
        callback?.onRawGnss(location)

        val isAccurate = location.accuracy <= GNSS_ACCURACY_THRESHOLD_M
        if (isAccurate) {
            if (currentState == FallbackState.FALLBACK_ACTIVE) {
                currentState = FallbackState.RECOVERING
            } else {
                currentState = FallbackState.GNSS_HEALTHY
            }
            currentLat = location.latitude
            currentLon = location.longitude
            currentSpeedMps = location.speed
            currentBearingDeg = location.bearing
            currentUncertaintyM = location.accuracy
            hasNavigationOrigin = true

            callback?.onLocationUpdate(location, false, currentState)
        } else {
            // GPS degraded (e.g. urban canyon multipath)
            currentState = FallbackState.FALLBACK_ACTIVE
        }
    }

    override fun onSensorChanged(event: SensorEvent) {
        callback?.onRawImu(event.sensor.type, event.timestamp, event.values.copyOf())
        val nowMs = SystemClock.elapsedRealtime()
        val timeSinceFix = nowMs - lastFixElapsedRealtimeMs

        // Check for GNSS Outage condition
        if (timeSinceFix > GNSS_TIMEOUT_MS) {
            currentState = FallbackState.FALLBACK_ACTIVE
        } else if (timeSinceFix > 1000L && currentState == FallbackState.GNSS_HEALTHY) {
            currentState = FallbackState.OUTAGE_PENDING
        }

        when (event.sensor.type) {
            Sensor.TYPE_GRAVITY -> {
                for (index in 0..2) latestGravity[index] = event.values[index].toDouble()
                checkMountShift(event.values[0], event.values[1], event.values[2])
            }
            Sensor.TYPE_LINEAR_ACCELERATION, Sensor.TYPE_ACCELEROMETER -> {
                for (index in 0..2) {
                    latestLinearAcceleration[index] = event.values[index].toDouble() -
                        if (hasLinearAccelerationSensor) 0.0 else latestGravity[index]
                }
                checkSurfaceShock(latestLinearAcceleration[2].toFloat())
            }
            Sensor.TYPE_GYROSCOPE -> {
                appendImuSample(event)
                // If in outage, dead reckon heading and forward position
                if (currentState == FallbackState.FALLBACK_ACTIVE && hasNavigationOrigin && imuWindow.size == 20) {
                    deadReckonStep(event)
                }
            }
        }
    }

    private fun deadReckonStep(gyroEvent: SensorEvent) {
        val dtS = if (lastImuTimestampNs > 0) {
            (gyroEvent.timestamp - lastImuTimestampNs) / 1_000_000_000.0
        } else 0.02
        lastImuTimestampNs = gyroEvent.timestamp

        // Integrate yaw rate (assume landscape or vertical mount alignment)
        val yawRateRad = gyroEvent.values[2].toDouble()
        currentBearingDeg = ((currentBearingDeg + Math.toDegrees(yawRateRad * dtS)) % 360.0 + 360.0).toFloat() % 360f

        val prediction = portableRunner.predict(summarizeImuWindow())
        currentSpeedMps = if (prediction.isStopped) 0.0f else prediction.speedMps.toFloat()

        // Propagate WGS-84 coordinates
        val distanceM = currentSpeedMps * dtS
        val headingRad = Math.toRadians(currentBearingDeg.toDouble())
        val deltaEast = distanceM * sin(headingRad)
        val deltaNorth = distanceM * cos(headingRad)

        // Flat-Earth local coordinate displacement to lat/lon
        val metersPerDegLat = 111132.954
        val metersPerDegLon = 111132.954 * cos(Math.toRadians(currentLat))

        currentLat += deltaNorth / metersPerDegLat
        currentLon += deltaEast / metersPerDegLon
        currentUncertaintyM += prediction.speedStdMps.toFloat() * dtS.toFloat()

        // Synthesize Android Location object
        val synthetic = Location("ContinuumIDR").apply {
            latitude = currentLat
            longitude = currentLon
            speed = currentSpeedMps
            bearing = currentBearingDeg
            accuracy = currentUncertaintyM
            time = System.currentTimeMillis()
            elapsedRealtimeNanos = gyroEvent.timestamp
        }

        callback?.onLocationUpdate(synthetic, true, currentState)
    }

    /** Matches continuum_idr.features.summarize_window: 6 channels × 7 statistics. */
    private fun summarizeImuWindow(): DoubleArray {
        val samples = imuWindow.toList()
        val features = DoubleArray(42)
        for (channel in 0 until 6) {
            val values = DoubleArray(samples.size) { samples[it][channel] }
            val mean = values.average()
            var variance = 0.0
            var energy = 0.0
            for (value in values) {
                variance += (value - mean) * (value - mean)
                energy += value * value
            }
            val offset = channel * 7
            features[offset] = mean
            features[offset + 1] = sqrt(variance / values.size)
            features[offset + 2] = values.minOrNull() ?: 0.0
            features[offset + 3] = values.maxOrNull() ?: 0.0
            features[offset + 4] = values.last()
            features[offset + 5] = values.last() - values.first()
            features[offset + 6] = sqrt(energy / values.size)
        }
        return features
    }

    private fun appendImuSample(gyroEvent: SensorEvent) {
        // The P0 model was trained at 10 Hz.  Keep its causal 2-second window
        // time-aligned even when the handset supplies 50–200 Hz sensor events.
        if (lastFeatureSampleTimestampNs != 0L &&
            gyroEvent.timestamp - lastFeatureSampleTimestampNs < 100_000_000L) return
        lastFeatureSampleTimestampNs = gyroEvent.timestamp
        val sample = DoubleArray(6)
        for (index in 0..2) {
            sample[index] = latestLinearAcceleration[index]
            sample[index + 3] = gyroEvent.values[index].toDouble()
        }
        if (imuWindow.size == 20) imuWindow.removeFirst()
        imuWindow.addLast(sample)
    }

    private fun checkMountShift(gx: Float, gy: Float, gz: Float) {
        if (!isRefGravitySet) {
            refGravityX = gx
            refGravityY = gy
            refGravityZ = gz
            isRefGravitySet = true
            return
        }

        val normRef = sqrt(refGravityX * refGravityX + refGravityY * refGravityY + refGravityZ * refGravityZ)
        val normCur = sqrt(gx * gx + gy * gy + gz * gz)
        if (normRef > 1f && normCur > 1f) {
            val dot = (refGravityX * gx + refGravityY * gy + refGravityZ * gz) / (normRef * normCur)
            val angleDeg = Math.toDegrees(Math.acos(dot.coerceIn(-1f, 1f).toDouble()))
            if (angleDeg > 15.0) {
                callback?.onMountShiftDetected()
            }
        }
    }

    private fun checkSurfaceShock(verticalLinearAcceleration: Float) {
        if (verticalLinearAcceleration > 4.5f) {
            callback?.onSurfaceAnomaly("SPEED_BREAKER", verticalLinearAcceleration.toDouble() / 12.0)
        } else if (verticalLinearAcceleration < -4.0f) {
            callback?.onSurfaceAnomaly("POTHOLE", Math.abs(verticalLinearAcceleration).toDouble() / 14.0)
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
    @Deprecated("Deprecated in Java")
    override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) {}
    override fun onProviderEnabled(provider: String) {}
    override fun onProviderDisabled(provider: String) {}
}
