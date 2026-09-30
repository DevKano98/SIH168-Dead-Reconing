package ai.continuum.idr

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class ParityTest {

    private lateinit var runner: PortableTreeRunner
    private lateinit var fixtureJson: JSONObject

    @Before
    fun setup() {
        val modelStream = javaClass.classLoader?.getResourceAsStream("motion_portable.json")
        assertNotNull("motion_portable.json must exist in test resources", modelStream)
        val modelText = modelStream!!.bufferedReader().use { it.readText() }
        runner = PortableTreeRunner.fromJsonString(modelText)

        val fixtureStream = javaClass.classLoader?.getResourceAsStream("parity_fixture.json")
        assertNotNull("parity_fixture.json must exist in test resources", fixtureStream)
        val fixtureText = fixtureStream!!.bufferedReader().use { it.readText() }
        fixtureJson = JSONObject(fixtureText)
    }

    @Test
    fun testPythonKotlinNumericalParityOnMultiStageFixture() {
        assertEquals("1.0.0", fixtureJson.getString("version"))
        val evaluations = fixtureJson.getJSONArray("evaluations")
        assertTrue("Fixture must contain evaluation checkpoints", evaluations.length() > 0)

        val tolerance = 1e-4

        for (i in 0 until evaluations.length()) {
            val ev = evaluations.getJSONObject(i)
            val stepIndex = ev.getInt("step_index")
            val featArray = ev.getJSONArray("features_42")
            val features = DoubleArray(featArray.length()) { featArray.getDouble(it) }

            val pred = runner.predict(features)

            val expectedSpeed = ev.getDouble("expected_speed_mps")
            val expectedStopProb = ev.getDouble("expected_stop_probability")
            val expectedIsStopped = ev.getBoolean("expected_is_stopped")
            val expectedUncertStd = ev.getDouble("expected_uncertainty_std_mps")

            assertEquals(
                "Step $stepIndex: Speed prediction divergence between Python and Kotlin exceeds $tolerance m/s",
                expectedSpeed,
                pred.speedMps,
                tolerance
            )

            assertEquals(
                "Step $stepIndex: Stop probability divergence between Python and Kotlin exceeds $tolerance",
                expectedStopProb,
                pred.stopProbability,
                tolerance
            )

            assertEquals(
                "Step $stepIndex: Stop binary classification state mismatch",
                expectedIsStopped,
                pred.isStopped
            )

            assertEquals(
                "Step $stepIndex: Uncertainty estimation divergence",
                expectedUncertStd,
                pred.speedStdMps,
                tolerance
            )
        }
    }
}
