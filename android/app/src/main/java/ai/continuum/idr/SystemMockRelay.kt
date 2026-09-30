package ai.continuum.idr

import android.content.Context
import android.location.Criteria
import android.location.Location
import android.location.LocationManager
import android.os.Build
import android.os.SystemClock
import android.util.Log

/**
 * Feeds dead-reckoned fallback coordinates directly into the Android OS GPS provider
 * via Android's Test/Mock Location Provider framework.
 *
 * When active, external navigation apps like Google Maps, Waze, and Uber running on the phone
 * will transparently follow Continuum's inertial trajectory during GNSS outages (tunnels, basements).
 */
class SystemMockRelay(private val context: Context) {

    private val locationManager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
    var isRelayActive = false
        private set
    var lastError: String? = null
        private set

    fun startRelay(): Boolean {
        if (isRelayActive) return true
        lastError = null

        return try {
            try {
                locationManager.removeTestProvider(LocationManager.GPS_PROVIDER)
            } catch (ignored: Exception) {}

            locationManager.addTestProvider(
                LocationManager.GPS_PROVIDER,
                /* requiresNetwork = */ false,
                /* requiresSatellite = */ true,
                /* requiresCell = */ false,
                /* hasMonetaryCost = */ false,
                /* supportsAltitude = */ true,
                /* supportsSpeed = */ true,
                /* supportsBearing = */ true,
                Criteria.POWER_LOW,
                Criteria.ACCURACY_FINE
            )
            locationManager.setTestProviderEnabled(LocationManager.GPS_PROVIDER, true)
            isRelayActive = true
            Log.i("SystemMockRelay", "Mock GPS Provider successfully registered")
            true
        } catch (e: SecurityException) {
            lastError = "Enable 'Select mock location app' -> 'Continuum IDR' in Android Developer Options"
            Log.w("SystemMockRelay", lastError, e)
            isRelayActive = false
            false
        } catch (e: Exception) {
            lastError = "Could not register mock GPS: ${e.message}"
            Log.w("SystemMockRelay", lastError, e)
            isRelayActive = false
            false
        }
    }

    fun pushLocation(location: Location) {
        if (!isRelayActive) return
        try {
            val synthetic = Location(LocationManager.GPS_PROVIDER).apply {
                latitude = location.latitude
                longitude = location.longitude
                altitude = if (location.hasAltitude()) location.altitude else 100.0
                speed = location.speed
                bearing = location.bearing
                accuracy = location.accuracy.coerceAtLeast(2.0f)
                time = System.currentTimeMillis()
                elapsedRealtimeNanos = SystemClock.elapsedRealtimeNanos()
                if (Build.VERSION.SDK_INT >= 26) {
                    verticalAccuracyMeters = 3.0f
                    speedAccuracyMetersPerSecond = 0.5f
                    bearingAccuracyDegrees = 3.0f
                }
            }
            locationManager.setTestProviderLocation(LocationManager.GPS_PROVIDER, synthetic)
        } catch (e: Exception) {
            Log.w("SystemMockRelay", "Failed to push mock location: ${e.message}")
        }
    }

    fun stopRelay() {
        if (!isRelayActive) return
        try {
            locationManager.setTestProviderEnabled(LocationManager.GPS_PROVIDER, false)
            locationManager.removeTestProvider(LocationManager.GPS_PROVIDER)
        } catch (ignored: Exception) {}
        isRelayActive = false
    }
}
