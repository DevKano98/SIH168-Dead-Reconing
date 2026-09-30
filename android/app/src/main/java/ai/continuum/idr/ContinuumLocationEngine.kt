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
import kotlin.math.abs
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
    private val portableRunner: PortableTreeRunner,
    var vehicleProfile: VehicleProfile = VehicleProfile.CAR,
    var roadGraphPack: RoadGraphPack? = null
) : LocationListener, SensorEventListener {

    enum class FallbackState {
        GNSS_HEALTHY,
        OUTAGE_PENDING,
        FALLBACK_ACTIVE,
        RECOVERING
    }

    enum class VehicleProfile {
        CAR,
        MOTORCYCLE,
        PARKING,
        EXTERNAL_IMU
    }

    data class EngineDiagnostics(
        val imuSamplesCount: Long,
        val gnssFixesCount: Long,
        val deadReckonStepsCount: Long,
        val lastInferenceLatencyUs: Long,
        val avgInferenceLatencyUs: Long,
        val lastMapMatchLatencyUs: Long,
        val avgMapMatchLatencyUs: Long,
        val estimatedMemoryKb: Long,
        val currentProfile: String,
        val currentState: String
    )

    interface LocationUpdateCallback {
        fun onLocationUpdate(location: Location, isFallback: Boolean, state: FallbackState)
        fun onLocationUpdate(location: Location, isFallback: Boolean, state: FallbackState, matchResult: MapMatchResult?) {
            onLocationUpdate(location, isFallback, state)
        }
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

    var currentLat = 0.0
        private set
    var currentLon = 0.0
        private set
    var currentSpeedMps = 0.0f
        private set
    var currentBearingDeg = 0.0f
        private set
    var currentUncertaintyM = 5.0f
        private set
    var hasNavigationOrigin = false
        private set
    var latestMatchResult: MapMatchResult? = null
        private set

    // Performance & Diagnostics instrumentation
    var imuSamplesCount = 0L
        private set
    var gnssFixesCount = 0L
        private set
    var deadReckonStepsCount = 0L
        private set
    var lastInferenceLatencyUs = 0L
        private set
    var totalInferenceLatencyUs = 0L
        private set
    var lastMapMatchLatencyUs = 0L
        private set
    var totalMapMatchLatencyUs = 0L
        private set

    fun getDiagnostics(): EngineDiagnostics {
        val avgInf = if (deadReckonStepsCount > 0) totalInferenceLatencyUs / deadReckonStepsCount else 0L
        val avgMm = if (deadReckonStepsCount > 0) totalMapMatchLatencyUs / deadReckonStepsCount else 0L
        val runtime = Runtime.getRuntime()
        val memKb = (runtime.totalMemory() - runtime.freeMemory()) / 1024L
        return EngineDiagnostics(
            imuSamplesCount = imuSamplesCount,
            gnssFixesCount = gnssFixesCount,
            deadReckonStepsCount = deadReckonStepsCount,
            lastInferenceLatencyUs = lastInferenceLatencyUs,
            avgInferenceLatencyUs = avgInf,
            lastMapMatchLatencyUs = lastMapMatchLatencyUs,
            avgMapMatchLatencyUs = avgMm,
            estimatedMemoryKb = memKb,
            currentProfile = vehicleProfile.name,
            currentState = currentState.name
        )
    }

    // Recovery blending
    private var recoveryStartRealtimeMs = 0L
    private val RECOVERY_DURATION_MS = 2500L
    private var recoverySourceLat = 0.0
    private var recoverySourceLon = 0.0

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

    // Motorcycle Lean Angle state
    var currentLeanAngleDeg = 0.0
        private set

    // Parking crawl / reverse detection
    private var isReverseGearDetected = false

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

        // 2. Register IMU Sensors
        val linearAccel = sensorManager.getDefaultSensor(Sensor.TYPE_LINEAR_ACCELERATION)
        val accel = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        val gyro = sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE)
        val gravity = sensorManager.getDefaultSensor(Sensor.TYPE_GRAVITY)

        hasLinearAccelerationSensor = linearAccel != null
        val delay = if (vehicleProfile == VehicleProfile.EXTERNAL_IMU) SensorManager.SENSOR_DELAY_FASTEST else SensorManager.SENSOR_DELAY_GAME
        (linearAccel ?: accel)?.let { sensorManager.registerListener(this, it, delay) }
        gyro?.let { sensorManager.registerListener(this, it, delay) }
        gravity?.let { sensorManager.registerListener(this, it, delay) }
    }

    fun stop() {
        if (!isTracking) return
        isTracking = false
        locationManager.removeUpdates(this)
        sensorManager.unregisterListener(this)
        imuWindow.clear()
    }

    override fun onLocationChanged(location: Location) {
        gnssFixesCount++
        val nowMs = SystemClock.elapsedRealtime()
        lastFixElapsedRealtimeMs = nowMs
        callback?.onRawGnss(location)

        val isAccurate = location.accuracy <= GNSS_ACCURACY_THRESHOLD_M
        if (isAccurate) {
            if (currentState == FallbackState.FALLBACK_ACTIVE) {
                // Initiate smooth recovery blending
                currentState = FallbackState.RECOVERING
                recoveryStartRealtimeMs = nowMs
                recoverySourceLat = currentLat
                recoverySourceLon = currentLon
            }

            if (currentState == FallbackState.RECOVERING) {
                val elapsedRecovery = nowMs - recoveryStartRealtimeMs
                if (elapsedRecovery >= RECOVERY_DURATION_MS) {
                    currentState = FallbackState.GNSS_HEALTHY
                    currentLat = location.latitude
                    currentLon = location.longitude
                } else {
                    val alpha = (elapsedRecovery.toDouble() / RECOVERY_DURATION_MS).coerceIn(0.0, 1.0)
                    currentLat = (1.0 - alpha) * recoverySourceLat + alpha * location.latitude
                    currentLon = (1.0 - alpha) * recoverySourceLon + alpha * location.longitude
                }
            } else {
                currentState = FallbackState.GNSS_HEALTHY
                currentLat = location.latitude
                currentLon = location.longitude
            }

            currentSpeedMps = location.speed
            if (location.hasBearing() && location.speed >= 1.5f) {
                currentBearingDeg = location.bearing
            }
            currentUncertaintyM = location.accuracy
            hasNavigationOrigin = true

            // Optional map matching update
            updateMapMatching()

            val blendedLocation = Location(location).apply {
                latitude = currentLat
                longitude = currentLon
                accuracy = currentUncertaintyM
            }
            callback?.onLocationUpdate(blendedLocation, false, currentState, latestMatchResult)
        } else {
            // Degraded accuracy / multipath
            currentState = FallbackState.FALLBACK_ACTIVE
        }
    }

    override fun onSensorChanged(event: SensorEvent) {
        imuSamplesCount++
        callback?.onRawImu(event.sensor.type, event.timestamp, event.values.copyOf())
        val nowMs = SystemClock.elapsedRealtime()
        val timeSinceFix = nowMs - lastFixElapsedRealtimeMs

        // Check for GNSS Outage condition
        if (timeSinceFix > GNSS_TIMEOUT_MS) {
            if (currentState != FallbackState.FALLBACK_ACTIVE) {
                currentState = FallbackState.FALLBACK_ACTIVE
            }
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

                // Parking reverse detection: negative longitudinal acceleration when starting from stop
                if (vehicleProfile == VehicleProfile.PARKING && currentSpeedMps < 0.5f) {
                    if (latestLinearAcceleration[1] < -1.8) {
                        isReverseGearDetected = true
                    } else if (latestLinearAcceleration[1] > 1.2) {
                        isReverseGearDetected = false
                    }
                }
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
        deadReckonStepsCount++
        val dtS = if (lastImuTimestampNs > 0) {
            (gyroEvent.timestamp - lastImuTimestampNs) / 1_000_000_000.0
        } else 0.02
        lastImuTimestampNs = gyroEvent.timestamp

        // Integrate yaw rate
        val yawRateRad = gyroEvent.values[2].toDouble()
        val deltaBearingDeg = Math.toDegrees(yawRateRad * dtS)
        currentBearingDeg = (((currentBearingDeg + deltaBearingDeg) % 360.0 + 360.0) % 360.0).toFloat()

        // Predict speed from portable tree runner with microsecond latency measurement
        val t0Inf = System.nanoTime()
        val prediction = portableRunner.predict(summarizeImuWindow())
        lastInferenceLatencyUs = (System.nanoTime() - t0Inf) / 1000L
        totalInferenceLatencyUs += lastInferenceLatencyUs

        var predictedSpeed = if (prediction.isStopped) 0.0 else prediction.speedMps

        // Profile-specific modifications
        when (vehicleProfile) {
            VehicleProfile.MOTORCYCLE -> {
                // Lean angle compensation: theta = atan(v * omega / g)
                val g = 9.80665
                val leanRad = atan2(predictedSpeed * yawRateRad, g)
                currentLeanAngleDeg = Math.toDegrees(leanRad)
            }
            VehicleProfile.PARKING -> {
                if (predictedSpeed < 0.6) predictedSpeed = 0.0
                if (isReverseGearDetected && predictedSpeed > 0.0) {
                    // Reverse speed convention
                    predictedSpeed = -predictedSpeed
                }
            }
            else -> {
                currentLeanAngleDeg = 0.0
            }
        }

        currentSpeedMps = predictedSpeed.toFloat()

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
        currentUncertaintyM += (prediction.speedStdMps * dtS).toFloat()

        // Map Matching Soft Snapping if Pack Loaded with latency timing
        val t0Mm = System.nanoTime()
        updateMapMatching()
        lastMapMatchLatencyUs = (System.nanoTime() - t0Mm) / 1000L
        totalMapMatchLatencyUs += lastMapMatchLatencyUs
        latestMatchResult?.let { match ->
            if (match.matched && match.matchConfidence >= 0.70 && !match.isAmbiguous && match.snappedLat != null && match.snappedLon != null) {
                // Softly pull towards road centerline to suppress lateral gyro integration drift
                val snapWeight = 0.15
                currentLat = (1.0 - snapWeight) * currentLat + snapWeight * match.snappedLat
                currentLon = (1.0 - snapWeight) * currentLon + snapWeight * match.snappedLon

                // Align bearing if within reasonable difference (< 25 deg)
                match.roadHeadingDeg?.let { roadHeading ->
                    val diff = abs(((currentBearingDeg - roadHeading + 180.0) % 360.0 + 360.0) % 360.0 - 180.0)
                    if (diff < 25.0) {
                        currentBearingDeg = (currentBearingDeg * 0.96f + roadHeading.toFloat() * 0.04f)
                    }
                }
            }
        }

        // Synthesize Android Location object
        val synthetic = Location("ContinuumIDR").apply {
            latitude = currentLat
            longitude = currentLon
            speed = abs(currentSpeedMps)
            bearing = currentBearingDeg
            accuracy = currentUncertaintyM
            time = System.currentTimeMillis()
            elapsedRealtimeNanos = gyroEvent.timestamp
        }

        callback?.onLocationUpdate(synthetic, true, currentState, latestMatchResult)
    }

    private fun updateMapMatching() {
        val pack = roadGraphPack ?: return
        if (!hasNavigationOrigin) return
        latestMatchResult = pack.match(
            lat = currentLat,
            lon = currentLon,
            headingDeg = currentBearingDeg.toDouble(),
            speedMps = abs(currentSpeedMps.toDouble())
        )
    }

    /** Matches continuum_idr.features.summarize_window: 6 channels × 7 statistics. */
    fun summarizeImuWindow(): DoubleArray {
        val samples = imuWindow.toList()
        val features = DoubleArray(42)
        if (samples.isEmpty()) return features
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
        val minIntervalNs = if (vehicleProfile == VehicleProfile.EXTERNAL_IMU) 10_000_000L else 100_000_000L
        if (lastFeatureSampleTimestampNs != 0L &&
            gyroEvent.timestamp - lastFeatureSampleTimestampNs < minIntervalNs) return
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
            callback?.onSurfaceAnomaly("POTHOLE", abs(verticalLinearAcceleration).toDouble() / 14.0)
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
    @Deprecated("Deprecated in Java")
    override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) {}
    override fun onProviderEnabled(provider: String) {}
    override fun onProviderDisabled(provider: String) {}
}
