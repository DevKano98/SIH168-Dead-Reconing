import Foundation

/// Evaluates the JSON bundle written by continuum_idr.portable_model in pure Swift.
/// Zero external dependencies, sub-microsecond tree traversal.
public final class PortableTreeRunner {

    public struct TreeNode {
        public let value: Double?
        public let featureIndex: Int
        public let threshold: Double
        public let leftChild: Int
        public let rightChild: Int

        public init(value: Double? = nil, featureIndex: Int = -1, threshold: Double = 0.0, leftChild: Int = -1, rightChild: Int = -1) {
            self.value = value
            self.featureIndex = featureIndex
            self.threshold = threshold
            self.leftChild = leftChild
            self.rightChild = rightChild
        }
    }

    public struct Prediction {
        public let speedMps: Double
        public let speedStdMps: Double
        public let isStopped: Bool
        public let stopProbability: Double

        public init(speedMps: Double, speedStdMps: Double, isStopped: Bool, stopProbability: Double) {
            self.speedMps = speedMps
            self.speedStdMps = speedStdMps
            self.isStopped = isStopped
            self.stopProbability = stopProbability
        }
    }

    public let modelId: String
    public let featureNames: [String]
    private let speedTrees: [[TreeNode]]
    private let speedBaseline: Double
    private let stopWeights: [Double]?
    private let stopIntercept: Double
    private let uncertaintyEdges: [Double]
    private let uncertaintyValues: [Double]

    public init(
        modelId: String,
        featureNames: [String],
        speedTrees: [[TreeNode]],
        speedBaseline: Double,
        stopWeights: [Double]?,
        stopIntercept: Double,
        uncertaintyEdges: [Double],
        uncertaintyValues: [Double]
    ) {
        self.modelId = modelId
        self.featureNames = featureNames
        self.speedTrees = speedTrees
        self.speedBaseline = speedBaseline
        self.stopWeights = stopWeights
        self.stopIntercept = stopIntercept
        self.uncertaintyEdges = uncertaintyEdges
        self.uncertaintyValues = uncertaintyValues
    }

    public static func fromJsonData(_ data: Data) throws -> PortableTreeRunner {
        guard let root = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw NSError(domain: "PortableTreeRunner", code: 1, userInfo: [NSLocalizedDescriptionKey: "Invalid JSON root"])
        }
        return try fromDictionary(root)
    }

    public static func fromJsonString(_ jsonStr: String) throws -> PortableTreeRunner {
        guard let data = jsonStr.data(using: .utf8) else {
            throw NSError(domain: "PortableTreeRunner", code: 2, userInfo: [NSLocalizedDescriptionKey: "Invalid UTF-8 encoding"])
        }
        return try fromJsonData(data)
    }

    public static func fromDictionary(_ root: [String: Any]) throws -> PortableTreeRunner {
        let manifest = root["manifest"] as? [String: Any] ?? [:]
        let rawFeatures = (root["feature_names"] as? [String]) ?? (manifest["feature_names"] as? [String]) ?? []
        let modelId = (root["model_id"] as? String) ?? (manifest["model_id"] as? String) ?? "portable-model"

        let rawTrees = (root["speed_trees"] as? [[[String: Any]]]) ?? []
        var parsedTrees: [[TreeNode]] = []
        parsedTrees.reserveCapacity(rawTrees.count)

        for treeNodes in rawTrees {
            var tree: [TreeNode] = []
            tree.reserveCapacity(treeNodes.count)
            for nodeDict in treeNodes {
                if let v = nodeDict["v"] as? NSNumber {
                    tree.append(TreeNode(value: v.doubleValue))
                } else {
                    let f = (nodeDict["f"] as? NSNumber)?.intValue ?? -1
                    let th = (nodeDict["th"] as? NSNumber)?.doubleValue ?? 0.0
                    let l = (nodeDict["l"] as? NSNumber)?.intValue ?? -1
                    let r = (nodeDict["r"] as? NSNumber)?.intValue ?? -1
                    tree.append(TreeNode(value: nil, featureIndex: f, threshold: th, leftChild: l, rightChild: r))
                }
            }
            parsedTrees.append(tree)
        }

        let speedBaseline = (root["speed_mean"] as? NSNumber)?.doubleValue ?? 0.0
        let stopWeightsRaw = root["stop_linear_weights"] as? [NSNumber]
        let stopWeights = stopWeightsRaw?.map { $0.doubleValue }

        let stopIntercept = (root["stop_linear_intercept"] as? NSNumber)?.doubleValue
            ?? (root["stop_mean"] as? NSNumber)?.doubleValue
            ?? 0.0

        let edgesRaw = (manifest["uncertainty_bins_mps"] as? [NSNumber]) ?? []
        let edges = edgesRaw.map { $0.doubleValue }

        let valuesRaw = (manifest["uncertainty_std_mps"] as? [NSNumber]) ?? []
        let values = valuesRaw.map { $0.doubleValue }

        return PortableTreeRunner(
            modelId: modelId,
            featureNames: rawFeatures,
            speedTrees: parsedTrees,
            speedBaseline: speedBaseline,
            stopWeights: stopWeights,
            stopIntercept: stopIntercept,
            uncertaintyEdges: edges,
            uncertaintyValues: values
        )
    }

    public func predict(_ features: [Double]) -> Prediction {
        precondition(features.count == featureNames.count, "expected \(featureNames.count) features, got \(features.count)")

        var speed = speedBaseline
        for tree in speedTrees {
            speed += evaluateTree(tree, features: features)
        }
        speed = min(max(speed, 0.0), 55.0)

        let logit: Double
        if let weights = stopWeights {
            var sum = stopIntercept
            for i in 0..<min(weights.count, features.count) {
                sum += weights[i] * features[i]
            }
            logit = sum
        } else {
            logit = 0.0
        }

        let stopProbability = 1.0 / (1.0 + exp(-logit))
        let stopped = stopProbability >= 0.5

        return Prediction(
            speedMps: speed,
            speedStdMps: uncertaintyFor(speed),
            isStopped: stopped,
            stopProbability: stopProbability
        )
    }

    private func evaluateTree(_ tree: [TreeNode], features: [Double]) -> Double {
        var nodeIndex = 0
        while true {
            guard nodeIndex >= 0 && nodeIndex < tree.count else {
                return 0.0
            }
            let node = tree[nodeIndex]
            if let v = node.value {
                return v
            }
            if features[node.featureIndex] <= node.threshold {
                nodeIndex = node.leftChild
            } else {
                nodeIndex = node.rightChild
            }
        }
    }

    private func uncertaintyFor(_ speed: Double) -> Double {
        if uncertaintyEdges.count < 2 || uncertaintyValues.isEmpty {
            return max(0.35, 0.08 * speed + 0.2)
        }
        var foundIndex = -1
        for (i, edge) in uncertaintyEdges.enumerated() {
            if speed >= edge {
                foundIndex = i
            }
        }
        if foundIndex < 0 {
            foundIndex = 0
        }
        let clampedIndex = min(max(foundIndex, 0), uncertaintyValues.count - 1)
        return uncertaintyValues[clampedIndex]
    }
}
