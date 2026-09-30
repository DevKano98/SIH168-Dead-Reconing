package ai.continuum.idr

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class RoadGraphPackTest {

    private lateinit var pack: RoadGraphPack

    @Before
    fun setup() {
        // Construct a clean test road pack with:
        // Main corridor (heading 0 deg / North, from (0,0) to (0, 1000m))
        // Parallel service road (offset 20m East, from (20, 0) to (20, 1000m))
        // Diverging diagonal ramp (from (0, 500) to (100, 800))
        val sampleJson = """
        {
          "format_version": "1.0.0",
          "name": "Unit Test Corridor",
          "cell_size_m": 100.0,
          "origin_lat": 12.8450,
          "origin_lon": 77.6600,
          "nodes": [
            {"id": "m0", "lat": 12.8450, "lon": 77.6600, "east_m": 0.0, "north_m": 0.0},
            {"id": "m1", "lat": 12.8495, "lon": 77.6600, "east_m": 0.0, "north_m": 500.0},
            {"id": "m2", "lat": 12.8540, "lon": 77.6600, "east_m": 0.0, "north_m": 1000.0},
            {"id": "s0", "lat": 12.8450, "lon": 77.66018, "east_m": 20.0, "north_m": 0.0},
            {"id": "s1", "lat": 12.8540, "lon": 77.66018, "east_m": 20.0, "north_m": 1000.0}
          ],
          "segments": [
            {
              "id": "main_0_500",
              "from_node": "m0",
              "to_node": "m1",
              "heading_deg": 0.0,
              "length_m": 500.0,
              "speed_limit_mps": 22.0,
              "lane_count": 3,
              "road_type": "motorway",
              "one_way": true
            },
            {
              "id": "main_500_1000",
              "from_node": "m1",
              "to_node": "m2",
              "heading_deg": 0.0,
              "length_m": 500.0,
              "speed_limit_mps": 22.0,
              "lane_count": 3,
              "road_type": "motorway",
              "one_way": true
            },
            {
              "id": "service_0_1000",
              "from_node": "s0",
              "to_node": "s1",
              "heading_deg": 0.0,
              "length_m": 1000.0,
              "speed_limit_mps": 10.0,
              "lane_count": 1,
              "road_type": "service",
              "one_way": false
            }
          ]
        }
        """.trimIndent()
        pack = RoadGraphPack.fromJsonString(sampleJson)
    }

    @Test
    fun testPackParsingAndCoordinateConversions() {
        assertEquals("Unit Test Corridor", pack.name)
        assertEquals(5, pack.nodes.size)
        assertEquals(3, pack.segments.size)

        // Test ENU roundtrip
        val (e, n) = pack.toEnu(12.8450, 77.6600)
        assertEquals(0.0, e, 1e-3)
        assertEquals(0.0, n, 1e-3)

        val (latRound, lonRound) = pack.toWgs84(0.0, 500.0)
        val (e2, n2) = pack.toEnu(latRound, lonRound)
        assertEquals(0.0, e2, 1e-3)
        assertEquals(500.0, n2, 1e-3)
    }

    @Test
    fun testPointProjectionOntoSegment() {
        // Project (5, 250) onto segment (0,0)-(0,500)
        val proj = pack.projectPointToSegment(5.0, 250.0, 0.0, 0.0, 0.0, 500.0)
        val sx = proj[0]
        val sy = proj[1]
        val crossDist = proj[2]
        val alongDist = proj[3]

        assertEquals(0.0, sx, 1e-6)
        assertEquals(250.0, sy, 1e-6)
        assertEquals(5.0, crossDist, 1e-6)
        assertEquals(250.0, alongDist, 1e-6)
    }

    @Test
    fun testRoadMatchingOnMainCorridor() {
        // Vehicle at east=2.0m, north=200m, heading=0 deg, speed=15 m/s
        val (vLat, vLon) = pack.toWgs84(2.0, 200.0)
        val match = pack.match(vLat, vLon, headingDeg = 0.0, speedMps = 15.0)

        assertTrue("Expected matched road", match.matched)
        assertEquals("main_0_500", match.segmentId)
        assertEquals(2.0, match.crossTrackErrorM, 0.1)
        assertEquals(200.0, match.alongTrackDistanceM, 0.1)
        assertTrue("High confidence expected on clear match", match.matchConfidence > 0.5)
        assertFalse("Should not be ambiguous when clearly on main road", match.isAmbiguous)
    }

    @Test
    fun testAmbiguityDetectionBetweenParallelRoads() {
        // Vehicle midway between main road (east=0) and service road (east=20) at east=10.0m
        val (vLat, vLon) = pack.toWgs84(10.0, 300.0)
        val match = pack.match(vLat, vLon, headingDeg = 0.0, speedMps = 10.0)

        assertTrue(match.matched)
        assertTrue("Midpoint between parallel roads must flag ambiguity", match.isAmbiguous)
        assertEquals(1, match.alternativeSegments.size)
    }

    @Test
    fun testHeadingDiscriminationOnOppositeDirection() {
        // Vehicle near main road (one-way North) but travelling South (heading 180 deg)
        val (vLat, vLon) = pack.toWgs84(5.0, 300.0)
        val match = pack.match(vLat, vLon, headingDeg = 180.0, speedMps = 10.0)

        // Main road is one-way North, so service road (bidirectional) should score higher or match
        if (match.matched) {
            assertEquals("service_0_1000", match.segmentId)
        }
    }
}
