import XCTest
@testable import ContinuumIDR

final class RoadGraphPackTests: XCTestCase {

    var pack: RoadGraphPack!

    override func setUpWithError() throws {
        try super.setUpWithError()

        let sampleJson = """
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
        """

        pack = try RoadGraphPack.fromJsonString(sampleJson)
    }

    func testPackParsingAndCoordinateConversions() {
        XCTAssertEqual(pack.name, "Unit Test Corridor")
        XCTAssertEqual(pack.nodes.count, 5)
        XCTAssertEqual(pack.segments.count, 3)

        // Test ENU roundtrip at origin
        let (e, n) = pack.toEnu(lat: 12.8450, lon: 77.6600)
        XCTAssertEqual(e, 0.0, accuracy: 1e-3)
        XCTAssertEqual(n, 0.0, accuracy: 1e-3)

        // Test WGS84 roundtrip
        let (latRound, lonRound) = pack.toWgs84(eastM: 0.0, northM: 500.0)
        let (e2, n2) = pack.toEnu(lat: latRound, lon: lonRound)
        XCTAssertEqual(e2, 0.0, accuracy: 1e-3)
        XCTAssertEqual(n2, 500.0, accuracy: 1e-3)
    }

    func testPointProjectionOntoSegment() {
        // Project (5, 250) onto segment (0,0)-(0,500)
        let proj = pack.projectPointToSegment(px: 5.0, py: 250.0, x1: 0.0, y1: 0.0, x2: 0.0, y2: 500.0)
        XCTAssertEqual(proj.sx, 0.0, accuracy: 1e-6)
        XCTAssertEqual(proj.sy, 250.0, accuracy: 1e-6)
        XCTAssertEqual(proj.crossTrackDist, 5.0, accuracy: 1e-6)
        XCTAssertEqual(proj.alongTrackDist, 250.0, accuracy: 1e-6)
    }

    func testRoadMatchingOnMainCorridor() {
        let (vLat, vLon) = pack.toWgs84(eastM: 2.0, northM: 200.0)
        let match = pack.match(lat: vLat, lon: vLon, headingDeg: 0.0, speedMps: 15.0)

        XCTAssertTrue(match.matched, "Expected matched road")
        XCTAssertEqual(match.segmentId, "main_0_500")
        XCTAssertEqual(match.crossTrackErrorM, 2.0, accuracy: 0.1)
        XCTAssertEqual(match.alongTrackDistanceM, 200.0, accuracy: 0.1)
        XCTAssertGreaterThan(match.matchConfidence, 0.5)
        XCTAssertFalse(match.isAmbiguous)
    }

    func testAmbiguityDetectionBetweenParallelRoads() {
        let (vLat, vLon) = pack.toWgs84(eastM: 10.0, northM: 300.0)
        let match = pack.match(lat: vLat, lon: vLon, headingDeg: 0.0, speedMps: 10.0)

        XCTAssertTrue(match.matched)
        XCTAssertTrue(match.isAmbiguous, "Midpoint between parallel roads must flag ambiguity")
        XCTAssertEqual(match.alternativeSegments.count, 1)
    }
}
