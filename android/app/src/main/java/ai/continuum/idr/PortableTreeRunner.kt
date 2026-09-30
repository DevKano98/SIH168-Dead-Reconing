package ai.continuum.idr

import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.exp

/** Evaluates the JSON bundle written by continuum_idr.portable_model. */
class PortableTreeRunner(
    val modelId: String,
    val featureNames: List<String>,
    private val speedTrees: List<List<TreeNode>>,
    private val speedBaseline: Double,
    private val stopWeights: DoubleArray?,
    private val stopIntercept: Double,
    private val uncertaintyEdges: DoubleArray,
    private val uncertaintyValues: DoubleArray
) {
    data class TreeNode(
        val value: Double? = null,
        val featureIndex: Int = -1,
        val threshold: Double = 0.0,
        val leftChild: Int = -1,
        val rightChild: Int = -1
    )

    data class Prediction(
        val speedMps: Double,
        val speedStdMps: Double,
        val isStopped: Boolean,
        val stopProbability: Double
    )

    companion object {
        fun fromJsonString(jsonStr: String): PortableTreeRunner {
            val root = JSONObject(jsonStr)
            val manifest = root.optJSONObject("manifest") ?: JSONObject()
            val features = root.optJSONArray("feature_names") ?: manifest.getJSONArray("feature_names")
            return PortableTreeRunner(
                modelId = root.optString("model_id", manifest.optString("model_id", "portable-model")),
                featureNames = strings(features),
                speedTrees = parseTrees(root.optJSONArray("speed_trees") ?: JSONArray()),
                speedBaseline = root.optDouble("speed_mean", 0.0),
                stopWeights = doublesOrNull(root, "stop_linear_weights"),
                stopIntercept = root.optDouble("stop_linear_intercept", root.optDouble("stop_mean", 0.0)),
                uncertaintyEdges = doubles(manifest.optJSONArray("uncertainty_bins_mps") ?: JSONArray()),
                uncertaintyValues = doubles(manifest.optJSONArray("uncertainty_std_mps") ?: JSONArray())
            )
        }

        private fun strings(values: JSONArray): List<String> = List(values.length()) { values.getString(it) }
        private fun doubles(values: JSONArray): DoubleArray = DoubleArray(values.length()) { values.getDouble(it) }
        private fun doublesOrNull(obj: JSONObject, key: String): DoubleArray? =
            if (obj.isNull(key) || !obj.has(key)) null else doubles(obj.getJSONArray(key))

        private fun parseTrees(trees: JSONArray): List<List<TreeNode>> = List(trees.length()) { index ->
            val tree = trees.getJSONArray(index)
            List(tree.length()) { nodeIndex ->
                val node = tree.getJSONObject(nodeIndex)
                if (node.has("v")) TreeNode(value = node.getDouble("v"))
                else TreeNode(
                    featureIndex = node.getInt("f"), threshold = node.getDouble("th"),
                    leftChild = node.getInt("l"), rightChild = node.getInt("r")
                )
            }
        }
    }

    fun predict(features: DoubleArray): Prediction {
        require(features.size == featureNames.size) { "expected ${featureNames.size} features, got ${features.size}" }
        var speed = speedBaseline
        for (tree in speedTrees) speed += evaluateTree(tree, features)
        speed = speed.coerceIn(0.0, 55.0)
        val logit = if (stopWeights == null) 0.0 else
            stopIntercept + stopWeights.indices.sumOf { index -> stopWeights[index] * features[index] }
        val stopProbability = 1.0 / (1.0 + exp(-logit))
        val stopped = stopProbability >= 0.5
        return Prediction(speed, uncertaintyFor(speed), stopped, stopProbability)
    }

    private fun evaluateTree(tree: List<TreeNode>, features: DoubleArray): Double {
        var nodeIndex = 0
        while (true) {
            val node = tree[nodeIndex]
            node.value?.let { return it }
            nodeIndex = if (features[node.featureIndex] <= node.threshold) node.leftChild else node.rightChild
            check(nodeIndex in tree.indices) { "invalid portable tree child index" }
        }
    }

    private fun uncertaintyFor(speed: Double): Double {
        if (uncertaintyEdges.size < 2 || uncertaintyValues.isEmpty()) return maxOf(0.35, 0.08 * speed + 0.2)
        var index = uncertaintyEdges.indexOfLast { speed >= it }
        if (index < 0) index = 0
        return uncertaintyValues[index.coerceIn(0, uncertaintyValues.lastIndex)]
    }
}
