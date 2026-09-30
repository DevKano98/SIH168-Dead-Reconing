package ai.continuum.idr

import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import kotlin.math.sqrt

/**
 * Zero-dependency standalone decision tree ensemble runner for Android.
 * Executes Continuum IDR portable models directly on-device without
 * requiring Python, PyTorch, TensorFlow Lite, or scikit-learn.
 */
class PortableTreeRunner(
    val modelId: String,
    val featureNames: List<String>,
    private val speedTrees: List<TreeNode>,
    private val stopTrees: List<TreeNode>,
    private val speedBaseline: Double,
    private val stopBaseline: Double,
    private val speedLearningRate: Double = 0.07,
    private val stopLearningRate: Double = 0.07
) {

    data class TreeNode(
        val isLeaf: Boolean,
        val value: Double = 0.0,
        val featureIndex: Int = -1,
        val threshold: Double = 0.0,
        val leftChild: TreeNode? = null,
        val rightChild: TreeNode? = null
    )

    data class Prediction(
        val speedMps: Double,
        val isStopped: Boolean,
        val stopProbability: Double
    )

    companion object {
        fun fromJsonString(jsonStr: String): PortableTreeRunner {
            val root = JSONObject(jsonStr)
            val modelId = root.optString("model_id", "portable-model")
            val featArray = root.getJSONArray("feature_names")
            val features = mutableListOf<String>()
            for (i in 0 until featArray.length()) {
                features.add(featArray.getString(i))
            }

            val speedTreesJson = root.optJSONArray("speed_trees") ?: JSONArray()
            val stopTreesJson = root.optJSONArray("stop_trees") ?: JSONArray()
            val speedBaseline = root.optDouble("speed_baseline", 0.0)
            val stopBaseline = root.optDouble("stop_baseline", 0.0)

            val speedTrees = parseTrees(speedTreesJson)
            val stopTrees = parseTrees(stopTreesJson)

            return PortableTreeRunner(
                modelId = modelId,
                featureNames = features,
                speedTrees = speedTrees,
                stopTrees = stopTrees,
                speedBaseline = speedBaseline,
                stopBaseline = stopBaseline
            )
        }

        private fun parseTrees(array: JSONArray): List<TreeNode> {
            val list = mutableListOf<TreeNode>()
            for (i in 0 until array.length()) {
                val nodeJson = array.getJSONObject(i)
                list.add(parseNode(nodeJson))
            }
            return list
        }

        private fun parseNode(obj: JSONObject): TreeNode {
            if (obj.has("value")) {
                return TreeNode(isLeaf = true, value = obj.getDouble("value"))
            }
            val featIdx = obj.getInt("feature")
            val threshold = obj.getDouble("threshold")
            val left = parseNode(obj.getJSONObject("left"))
            val right = parseNode(obj.getJSONObject("right"))
            return TreeNode(
                isLeaf = false,
                featureIndex = featIdx,
                threshold = threshold,
                leftChild = left,
                rightChild = right
            )
        }
    }

    /**
     * Run prediction given raw feature vector.
     * Takes < 0.2 ms on modern ARM processors.
     */
    fun predict(features: DoubleArray): Prediction {
        var speedRaw = speedBaseline
        for (tree in speedTrees) {
            speedRaw += speedLearningRate * evaluateTree(tree, features)
        }
        val speedMps = speedRaw.coerceIn(0.0, 55.0)

        var stopRaw = stopBaseline
        for (tree in stopTrees) {
            stopRaw += stopLearningRate * evaluateTree(tree, features)
        }
        val stopProb = 1.0 / (1.0 + Math.exp(-stopRaw))
        val isStopped = stopProb >= 0.50 || speedMps < 0.35

        return Prediction(
            speedMps = if (isStopped) 0.0 else speedMps,
            isStopped = isStopped,
            stopProbability = stopProb
        )
    }

    private fun evaluateTree(node: TreeNode, features: DoubleArray): Double {
        if (node.isLeaf) return node.value
        val featVal = if (node.featureIndex in features.indices) features[node.featureIndex] else 0.0
        return if (featVal <= node.threshold) {
            evaluateTree(node.leftChild ?: return node.value, features)
        } else {
            evaluateTree(node.rightChild ?: return node.value, features)
        }
    }
}
