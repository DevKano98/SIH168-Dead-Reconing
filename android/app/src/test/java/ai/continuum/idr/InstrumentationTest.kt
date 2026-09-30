package ai.continuum.idr

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

class InstrumentationTest {

    @Test
    fun testEngineDiagnosticsDataClass() {
        val diag = ContinuumLocationEngine.EngineDiagnostics(
            imuSamplesCount = 100L,
            gnssFixesCount = 10L,
            deadReckonStepsCount = 20L,
            lastInferenceLatencyUs = 450L,
            avgInferenceLatencyUs = 420L,
            lastMapMatchLatencyUs = 120L,
            avgMapMatchLatencyUs = 110L,
            estimatedMemoryKb = 12400L,
            currentProfile = "CAR",
            currentState = "GNSS_HEALTHY"
        )

        assertEquals(100L, diag.imuSamplesCount)
        assertEquals(10L, diag.gnssFixesCount)
        assertEquals(20L, diag.deadReckonStepsCount)
        assertEquals(450L, diag.lastInferenceLatencyUs)
        assertEquals(420L, diag.avgInferenceLatencyUs)
        assertEquals(120L, diag.lastMapMatchLatencyUs)
        assertEquals(110L, diag.avgMapMatchLatencyUs)
        assertTrue(diag.estimatedMemoryKb > 0)
        assertEquals("CAR", diag.currentProfile)
        assertEquals("GNSS_HEALTHY", diag.currentState)
    }

    @Test
    fun testBleRelayStatsDataClass() {
        val stats = BleRelayStats(
            sentCount = 5L,
            receivedCount = 8L,
            relayedCount = 3L,
            duplicateCount = 2L,
            expiredCount = 1L
        )

        assertEquals(5L, stats.sentCount)
        assertEquals(8L, stats.receivedCount)
        assertEquals(3L, stats.relayedCount)
        assertEquals(2L, stats.duplicateCount)
        assertEquals(1L, stats.expiredCount)
    }

    @Test
    fun testTrafficHazardReport() {
        val hazard = TrafficHazardReport(
            hazardType = "POTHOLE",
            severity = 0.85,
            latitude = 12.9716,
            longitude = 77.5946,
            timestampMs = 1700000000000L,
            vehicleId = "test_vehicle"
        )

        assertEquals("POTHOLE", hazard.hazardType)
        assertEquals(0.85, hazard.severity, 1e-4)
        assertEquals(12.9716, hazard.latitude, 1e-4)
        assertEquals(77.5946, hazard.longitude, 1e-4)
        assertEquals("test_vehicle", hazard.vehicleId)
    }
}
