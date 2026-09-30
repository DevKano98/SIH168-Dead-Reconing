package ai.continuum.idr

import org.json.JSONObject
import java.io.InputStream
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.exp
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin
import kotlin.math.sqrt

data class RoadNode(
    val id: String,
    val lat: Double,
    val lon: Double,
    val eastM: Double,
    val northM: Double
)

data class RoadSegment(
    val id: String,
    val fromNode: String,
    val toNode: String,
    val startEastM: Double,
    val startNorthM: Double,
    val endEastM: Double,
    val endNorthM: Double,
    val headingDeg: Double,
    val lengthM: Double,
    val speedLimitMps: Double = 20.0,
    val laneCount: Int = 1,
    val roadType: String = "primary",
    val oneWay: Boolean = false
)

data class MapMatchResult(
    val matched: Boolean,
    val segmentId: String? = null,
    val snappedLat: Double? = null,
    val snappedLon: Double? = null,
    val snappedEastM: Double? = null,
    val snappedNorthM: Double? = null,
    val crossTrackErrorM: Double = Double.NaN,
    val alongTrackDistanceM: Double = Double.NaN,
    val roadHeadingDeg: Double? = null,
    val headingDivergenceDeg: Double? = null,
    val matchConfidence: Double = 0.0,
    val isAmbiguous: Boolean = false,
    val candidateCount: Int = 0,
    val alternativeSegments: List<String> = emptyList()
)

class RoadGraphPack(
    val name: String,
    val cellSizeM: Double,
    val originLat: Double,
    val originLon: Double,
    val nodes: Map<String, RoadNode>,
    val segments: Map<String, RoadSegment>
) {
    private val EARTH_RADIUS_M = 6378137.0
    private val originLatRad = Math.toRadians(originLat)
    private val grid = HashMap<Pair<Int, Int>, MutableList<String>>()
    private var lastMatchedSegmentId: String? = null

    init {
        // Build spatial index
        for (seg in segments.values) {
            val minE = min(seg.startEastM, seg.endEastM)
            val maxE = max(seg.startEastM, seg.endEastM)
            val minN = min(seg.startNorthM, seg.endNorthM)
            val maxN = max(seg.startNorthM, seg.endNorthM)

            val cMinX = cellCoord(minE)
            val cMaxX = cellCoord(maxE)
            val cMinY = cellCoord(minN)
            val cMaxY = cellCoord(maxN)

            for (cx in cMinX..cMaxX) {
                for (cy in cMinY..cMaxY) {
                    grid.getOrPut(Pair(cx, cy)) { ArrayList() }.add(seg.id)
                }
            }
        }
    }

    private fun cellCoord(valM: Double): Int = Math.floor(valM / cellSizeM).toInt()

    fun toEnu(lat: Double, lon: Double): Pair<Double, Double> {
        val east = Math.toRadians(lon - originLon) * EARTH_RADIUS_M * cos(originLatRad)
        val north = Math.toRadians(lat - originLat) * EARTH_RADIUS_M
        return Pair(east, north)
    }

    fun toWgs84(eastM: Double, northM: Double): Pair<Double, Double> {
        val lat = originLat + Math.toDegrees(northM / EARTH_RADIUS_M)
        val lon = originLon + Math.toDegrees(eastM / (EARTH_RADIUS_M * cos(originLatRad)))
        return Pair(lat, lon)
    }

    fun getCandidates(eastM: Double, northM: Double, radiusM: Double = 50.0): List<RoadSegment> {
        val cxMin = cellCoord(eastM - radiusM)
        val cxMax = cellCoord(eastM + radiusM)
        val cyMin = cellCoord(northM - radiusM)
        val cyMax = cellCoord(northM + radiusM)

        val seen = HashSet<String>()
        val result = ArrayList<RoadSegment>()

        for (cx in cxMin..cxMax) {
            for (cy in cyMin..cyMax) {
                grid[Pair(cx, cy)]?.let { segIds ->
                    for (id in segIds) {
                        if (seen.add(id)) {
                            segments[id]?.let { result.add(it) }
                        }
                    }
                }
            }
        }
        return result
    }

    fun projectPointToSegment(
        px: Double, py: Double,
        x1: Double, y1: Double,
        x2: Double, y2: Double
    ): DoubleArray {
        // Returns: [snappedX, snappedY, crossTrackDist, alongTrackDist]
        val dx = x2 - x1
        val dy = y2 - y1
        val lenSq = dx * dx + dy * dy
        if (lenSq < 1e-9) {
            val d = hypot(px - x1, py - y1)
            return doubleArrayOf(x1, y1, d, 0.0)
        }
        val t = ((px - x1) * dx + (py - y1) * dy) / lenSq
        val tClamped = max(0.0, min(1.0, t))
        val sx = x1 + tClamped * dx
        val sy = y1 + tClamped * dy

        val crossProd = dx * (py - y1) - dy * (px - x1)
        val signedCross = crossProd / sqrt(lenSq)
        val alongTrack = tClamped * sqrt(lenSq)

        return doubleArrayOf(sx, sy, abs(signedCross), alongTrack)
    }

    fun match(
        lat: Double,
        lon: Double,
        headingDeg: Double? = null,
        speedMps: Double? = null,
        searchRadiusM: Double = 40.0,
        sigmaDistM: Double = 12.0,
        sigmaHeadingDeg: Double = 25.0,
        minConfidenceThresh: Double = 0.20,
        ambiguityMargin: Double = 0.15
    ): MapMatchResult {
        val (eastM, northM) = toEnu(lat, lon)
        val candidates = getCandidates(eastM, northM, searchRadiusM)
        if (candidates.isEmpty()) {
            return MapMatchResult(matched = false, candidateCount = 0)
        }

        data class ScoredCandidate(
            val score: Double,
            val seg: RoadSegment,
            val sx: Double,
            val sy: Double,
            val crossDist: Double,
            val alongDist: Double
        )

        val scored = ArrayList<ScoredCandidate>()

        for (seg in candidates) {
            val proj = projectPointToSegment(eastM, northM, seg.startEastM, seg.startNorthM, seg.endEastM, seg.endNorthM)
            val sx = proj[0]
            val sy = proj[1]
            val crossDist = proj[2]
            val alongDist = proj[3]

            val pDist = exp(-0.5 * (crossDist / sigmaDistM) * (crossDist / sigmaDistM))
            var pHeading = 1.0
            if (headingDeg != null && java.lang.Double.isFinite(headingDeg) && (speedMps ?: 0.0) >= 1.5) {
                var diff = ((headingDeg - seg.headingDeg + 180.0) % 360.0 + 360.0) % 360.0 - 180.0
                if (!seg.oneWay) {
                    val oppDiff = ((headingDeg - (seg.headingDeg + 180.0) + 180.0) % 360.0 + 360.0) % 360.0 - 180.0
                    if (abs(oppDiff) < abs(diff)) {
                        diff = oppDiff
                    }
                }
                val headingDiv = abs(diff)
                pHeading = exp(-0.5 * (headingDiv / sigmaHeadingDeg) * (headingDiv / sigmaHeadingDeg))
            }

            val continuityBonus = if (seg.id == lastMatchedSegmentId) 1.25 else 1.0
            val totalScore = pDist * pHeading * continuityBonus
            scored.add(ScoredCandidate(totalScore, seg, sx, sy, crossDist, alongDist))
        }

        scored.sortByDescending { it.score }
        val best = scored[0]
        val scoreSum = scored.sumOf { it.score }
        val confidence = best.score / max(scoreSum, 1e-6)

        if (confidence < minConfidenceThresh || best.crossDist > searchRadiusM) {
            return MapMatchResult(
                matched = false,
                crossTrackErrorM = best.crossDist,
                alongTrackDistanceM = best.alongDist,
                roadHeadingDeg = best.seg.headingDeg,
                matchConfidence = confidence,
                candidateCount = scored.size
            )
        }

        var isAmbiguous = false
        val alternatives = ArrayList<String>()
        if (scored.size > 1) {
            val secondConf = scored[1].score / max(scoreSum, 1e-6)
            if ((confidence - secondConf) < ambiguityMargin) {
                isAmbiguous = true
                alternatives.add(scored[1].seg.id)
            }
        }

        lastMatchedSegmentId = best.seg.id
        val (snappedLat, snappedLon) = toWgs84(best.sx, best.sy)
        val headingDiv = if (headingDeg != null) {
            abs(((headingDeg - best.seg.headingDeg + 180.0) % 360.0 + 360.0) % 360.0 - 180.0)
        } else null

        return MapMatchResult(
            matched = true,
            segmentId = best.seg.id,
            snappedLat = snappedLat,
            snappedLon = snappedLon,
            snappedEastM = best.sx,
            snappedNorthM = best.sy,
            crossTrackErrorM = best.crossDist,
            alongTrackDistanceM = best.alongDist,
            roadHeadingDeg = best.seg.headingDeg,
            headingDivergenceDeg = headingDiv,
            matchConfidence = confidence,
            isAmbiguous = isAmbiguous,
            candidateCount = scored.size,
            alternativeSegments = alternatives
        )
    }

    companion object {
        fun fromInputStream(stream: InputStream): RoadGraphPack {
            val text = stream.bufferedReader().use { it.readText() }
            return fromJsonString(text)
        }

        fun fromJsonString(jsonStr: String): RoadGraphPack {
            val root = JSONObject(jsonStr)
            val name = root.optString("name", "road_pack")
            val cellSizeM = root.optDouble("cell_size_m", 100.0)
            val originLat = root.getDouble("origin_lat")
            val originLon = root.getDouble("origin_lon")

            val nodesMap = HashMap<String, RoadNode>()
            val nodesArr = root.getJSONArray("nodes")
            for (i in 0 until nodesArr.length()) {
                val obj = nodesArr.getJSONObject(i)
                val id = obj.getString("id")
                nodesMap[id] = RoadNode(
                    id = id,
                    lat = obj.getDouble("lat"),
                    lon = obj.getDouble("lon"),
                    eastM = obj.optDouble("east_m", 0.0),
                    northM = obj.optDouble("north_m", 0.0)
                )
            }

            val segmentsMap = HashMap<String, RoadSegment>()
            val segsArr = root.getJSONArray("segments")
            for (i in 0 until segsArr.length()) {
                val obj = segsArr.getJSONObject(i)
                val id = obj.getString("id")
                val fromNodeId = obj.getString("from_node")
                val toNodeId = obj.getString("to_node")
                val fromNode = nodesMap[fromNodeId] ?: continue
                val toNode = nodesMap[toNodeId] ?: continue

                segmentsMap[id] = RoadSegment(
                    id = id,
                    fromNode = fromNodeId,
                    toNode = toNodeId,
                    startEastM = fromNode.eastM,
                    startNorthM = fromNode.northM,
                    endEastM = toNode.eastM,
                    endNorthM = toNode.northM,
                    headingDeg = obj.optDouble("heading_deg", 0.0),
                    lengthM = obj.optDouble("length_m", hypot(toNode.eastM - fromNode.eastM, toNode.northM - fromNode.northM)),
                    speedLimitMps = obj.optDouble("speed_limit_mps", 20.0),
                    laneCount = obj.optInt("lane_count", 1),
                    roadType = obj.optString("road_type", "primary"),
                    oneWay = obj.optBoolean("one_way", false)
                )
            }

            return RoadGraphPack(
                name = name,
                cellSizeM = cellSizeM,
                originLat = originLat,
                originLon = originLon,
                nodes = nodesMap,
                segments = segmentsMap
            )
        }
    }
}
