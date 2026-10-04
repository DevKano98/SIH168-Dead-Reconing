import XCTest
@testable import ContinuumIDR

final class ParityTests: XCTestCase {

    var runner: PortableTreeRunner!
    var fixtureData: [String: Any]!

    override func setUpWithError() throws {
        try super.setUpWithError()

        // 1. Load motion_portable.json
        let testBundle = Bundle(for: type(of: self))
        let modelUrl = testBundle.url(forResource: "motion_portable", withExtension: "json")
            ?? Bundle.main.url(forResource: "motion_portable", withExtension: "json")

        guard let validModelUrl = modelUrl, let modelData = try? Data(contentsOf: validModelUrl) else {
            XCTFail("Could not locate motion_portable.json in test bundle or main bundle")
            return
        }
        runner = try PortableTreeRunner.fromJsonData(modelData)

        // 2. Load parity_fixture.json
        let fixtureUrl = testBundle.url(forResource: "parity_fixture", withExtension: "json")
            ?? Bundle.main.url(forResource: "parity_fixture", withExtension: "json")

        guard let validFixtureUrl = fixtureUrl, let fData = try? Data(contentsOf: validFixtureUrl),
              let json = try? JSONSerialization.jsonObject(with: fData) as? [String: Any] else {
            XCTFail("Could not locate or parse parity_fixture.json")
            return
        }
        fixtureData = json
    }

    func testPythonKotlinSwiftNumericalParity() throws {
        guard let runner = runner, let fixture = fixtureData else {
            XCTFail("Test setup incomplete")
            return
        }

        XCTAssertEqual(fixture["version"] as? String, "1.0.0")
        guard let evaluations = fixture["evaluations"] as? [[String: Any]] else {
            XCTFail("Fixture missing 'evaluations' array")
            return
        }
        XCTAssertGreaterThan(evaluations.count, 0, "Fixture must contain evaluation checkpoints")

        let tolerance: Double = 1e-4

        for ev in evaluations {
            guard let stepIndex = ev["step_index"] as? Int,
                  let featArray = ev["features_42"] as? [NSNumber],
                  let expectedSpeed = (ev["expected_speed_mps"] as? NSNumber)?.doubleValue,
                  let expectedStopProb = (ev["expected_stop_probability"] as? NSNumber)?.doubleValue,
                  let expectedIsStopped = ev["expected_is_stopped"] as? Bool,
                  let expectedUncert = (ev["expected_uncertainty_std_mps"] as? NSNumber)?.doubleValue else {
                XCTFail("Invalid evaluation item schema")
                continue
            }

            let features = featArray.map { $0.doubleValue }
            let pred = runner.predict(features)

            XCTAssertEqual(
                pred.speedMps,
                expectedSpeed,
                accuracy: tolerance,
                "Step \(stepIndex): Speed divergence between Python/Kotlin and Swift exceeds \(tolerance) m/s"
            )

            XCTAssertEqual(
                pred.stopProbability,
                expectedStopProb,
                accuracy: tolerance,
                "Step \(stepIndex): Stop probability divergence exceeds \(tolerance)"
            )

            XCTAssertEqual(
                pred.isStopped,
                expectedIsStopped,
                "Step \(stepIndex): Binary stop classification state mismatch"
            )

            XCTAssertEqual(
                pred.speedStdMps,
                expectedUncert,
                accuracy: tolerance,
                "Step \(stepIndex): Uncertainty estimation divergence"
            )
        }
    }
}
