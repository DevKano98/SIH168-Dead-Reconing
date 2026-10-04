import XCTest
@testable import ContinuumIDR

final class FeatureExtractionTests: XCTestCase {

    func testSummarizeImuWindowShapeAndValues() {
        // Construct dummy runner
        let runner = PortableTreeRunner(
            modelId: "test",
            featureNames: (0..<42).map { "feat_\($0)" },
            speedTrees: [],
            speedBaseline: 0.0,
            stopWeights: nil,
            stopIntercept: 0.0,
            uncertaintyEdges: [],
            uncertaintyValues: []
        )

        let engine = ContinuumLocationEngine(portableRunner: runner)

        // Empty window should yield 42 zeros
        let emptyFeats = engine.summarizeImuWindow()
        XCTAssertEqual(emptyFeats.count, 42)
        for f in emptyFeats {
            XCTAssertEqual(f, 0.0)
        }
    }
}
