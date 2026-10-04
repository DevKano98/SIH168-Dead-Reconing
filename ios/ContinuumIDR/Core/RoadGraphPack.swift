import Foundation

/// Topological road network pack with 2D spatial hash grid indexing
/// and Gaussian likelihood map matching.
public final class RoadGraphPack {

    public let name: String
    public let cellSizeM: Double
    public let originLat: Double
    public let originLon: Double
    public let nodes: [String: RoadNode]
    public let segments: [String: RoadSegment]

    private let earthRadiusM: Double = 6378137.0
    private let originLatRad: Double
    private var grid: [GridCell: [String]] = [:]
    private var lastMatchedSegmentId: String? = nil

    private struct GridCell: Hashable {
        let x: Int
        let y: Int
    }

    public init(
        name: String,
        cellSizeM: Double = 100.0,
        originLat: Double,
        originLon: Double,
        nodes: [String: RoadNode],
        segments: [String: RoadSegment]
    ) {
        self.name = name
        self.cellSizeM = cellSizeM
        self.originLat = originLat
        self.originLon = originLon
        self.nodes = nodes
        self.segments = segments
        self.originLatRad = originLat * .pi / 180.0

        buildSpatialIndex()
    }

    private func buildSpatialIndex() {
        grid.removeAll(keepingCapacity: true)
        for seg in segments.values {
            let minE = min(seg.startEastM, seg.endEastM)
            let maxE = max(seg.startEastM, seg.endEastM)
            let minN = min(seg.startNorthM, seg.endNorthM)
            let maxN = max(seg.startNorthM, seg.endNorthM)

            let cMinX = cellCoord(minE)
            let cMaxX = cellCoord(maxE)
            let cMinY = cellCoord(minN)
            let cMaxY = cellCoord(maxN)

            for cx in cMinX...cMaxX {
                for cy in cMinY...cMaxY {
                    let cell = GridCell(x: cx, y: cy)
                    if grid[cell] == nil {
                        grid[cell] = [seg.id]
                    } else {
                        grid[cell]?.append(seg.id)
                    }
                }
            }
        }
    }

    private func cellCoord(_ valM: Double) -> Int {
        return Int(floor(valM / cellSizeM))
    }

    public func toEnu(lat: Double, lon: Double) -> (eastM: Double, northM: Double) {
        let deg2rad = Double.pi / 180.0
        let east = (lon - originLon) * deg2rad * earthRadiusM * cos(originLatRad)
        let north = (lat - originLat) * deg2rad * earthRadiusM
        return (east, north)
    }

    public func toWgs84(eastM: Double, northM: Double) -> (lat: Double, lon: Double) {
        let rad2deg = 180.0 / Double.pi
        let lat = originLat + (northM / earthRadiusM) * rad2deg
        let lon = originLon + (eastM / (earthRadiusM * cos(originLatRad))) * rad2deg
        return (lat, lon)
    }

    public func getCandidates(eastM: Double, northM: Double, radiusM: Double = 50.0) -> [RoadSegment] {
        let cxMin = cellCoord(eastM - radiusM)
        let cxMax = cellCoord(eastM + radiusM)
        let cyMin = cellCoord(northM - radiusM)
        let cyMax = cellCoord(northM + radiusM)

        var seen = Set<String>()
        var results: [RoadSegment] = []

        for cx in cxMin...cxMax {
            for cy in cyMin...cyMax {
                if let segIds = grid[GridCell(x: cx, y: cy)] {
                    for id in segIds {
                        if seen.insert(id).inserted {
                            if let seg = segments[id] {
                                results.append(seg)
                            }
                        }
                    }
                }
            }
        }
        return results
    }

    public func projectPointToSegment(
        px: Double, py: Double,
        x1: Double, y1: Double,
        x2: Double, y2: Double
    ) -> (sx: Double, sy: Double, crossTrackDist: Double, alongTrackDist: Double) {
        let dx = x2 - x1
        let dy = y2 - y1
        let lenSq = dx * dx + dy * dy
        if lenSq < 1e-9 {
            let d = hypot(px - x1, py - y1)
            return (x1, y1, d, 0.0)
        }
        let t = ((px - x1) * dx + (py - y1) * dy) / lenSq
        let tClamped = max(0.0, min(1.0, t))
        let sx = x1 + tClamped * dx
        let sy = y1 + tClamped * dy

        let crossProd = dx * (py - y1) - dy * (px - x1)
        let signedCross = crossProd / sqrt(lenSq)
        let alongTrack = tClamped * sqrt(lenSq)

        return (sx, sy, abs(signedCross), alongTrack)
    }

    public func match(
        lat: Double,
        lon: Double,
        headingDeg: Double? = nil,
        speedMps: Double? = nil,
        searchRadiusM: Double = 40.0,
        sigmaDistM: Double = 12.0,
        sigmaHeadingDeg: Double = 25.0,
        minConfidenceThresh: Double = 0.20,
        ambiguityMargin: Double = 0.15
    ) -> MapMatchResult {
        let (eastM, northM) = toEnu(lat: lat, lon: lon)
        let candidates = getCandidates(eastM: eastM, northM: northM, radiusM: searchRadiusM)
        if candidates.isEmpty {
            return MapMatchResult(matched: false, candidateCount: 0)
        }

        struct ScoredCandidate {
            let score: Double
            let seg: RoadSegment
            let sx: Double
            let sy: Double
            let crossDist: Double
            let alongDist: Double
        }

        var scored: [ScoredCandidate] = []
        scored.reserveCapacity(candidates.count)

        for seg in candidates {
            let proj = projectPointToSegment(
                px: eastM, py: northM,
                x1: seg.startEastM, y1: seg.startNorthM,
                x2: seg.endEastM, y2: seg.endNorthM
            )

            let pDist = exp(-0.5 * (proj.crossTrackDist / sigmaDistM) * (proj.crossTrackDist / sigmaDistM))
            var pHeading = 1.0

            if let hdg = headingDeg, hdg.isFinite && (speedMps ?? 0.0) >= 1.5 {
                var diff = ((hdg - seg.headingDeg + 180.0).truncatingRemainder(dividingBy: 360.0) + 360.0).truncatingRemainder(dividingBy: 360.0) - 180.0
                if !seg.oneWay {
                    let oppDiff = ((hdg - (seg.headingDeg + 180.0) + 180.0).truncatingRemainder(dividingBy: 360.0) + 360.0).truncatingRemainder(dividingBy: 360.0) - 180.0
                    if abs(oppDiff) < abs(diff) {
                        diff = oppDiff
                    }
                }
                let headingDiv = abs(diff)
                pHeading = exp(-0.5 * (headingDiv / sigmaHeadingDeg) * (headingDiv / sigmaHeadingDeg))
            }

            let continuityBonus = (seg.id == lastMatchedSegmentId) ? 1.25 : 1.0
            let totalScore = pDist * pHeading * continuityBonus
            scored.append(ScoredCandidate(score: totalScore, seg: seg, sx: proj.sx, sy: proj.sy, crossDist: proj.crossTrackDist, alongDist: proj.alongTrackDist))
        }

        scored.sort { $0.score > $1.score }
        guard let best = scored.first else {
            return MapMatchResult(matched: false, candidateCount: 0)
        }

        let scoreSum = scored.reduce(0.0) { $0 + $1.score }
        let confidence = best.score / max(scoreSum, 1e-6)

        if confidence < minConfidenceThresh || best.crossDist > searchRadiusM {
            return MapMatchResult(
                matched: false,
                crossTrackErrorM: best.crossDist,
                alongTrackDistanceM: best.alongDist,
                roadHeadingDeg: best.seg.headingDeg,
                matchConfidence: confidence,
                candidateCount: scored.count
            )
        }

        var isAmbiguous = false
        var alternatives: [String] = []
        if scored.count > 1 {
            let secondConf = scored[1].score / max(scoreSum, 1e-6)
            if (confidence - secondConf) < ambiguityMargin {
                isAmbiguous = true
                alternatives.append(scored[1].seg.id)
            }
        }

        lastMatchedSegmentId = best.seg.id
        let (snappedLat, snappedLon) = toWgs84(eastM: best.sx, northM: best.sy)

        let headingDiv: Double?
        if let hdg = headingDeg {
            headingDiv = abs(((hdg - best.seg.headingDeg + 180.0).truncatingRemainder(dividingBy: 360.0) + 360.0).truncatingRemainder(dividingBy: 360.0) - 180.0)
        } else {
            headingDiv = nil
        }

        return MapMatchResult(
            matched: true,
            segmentId: best.seg.id,
            snappedLat: snappedLat,
            snappedLon: snappedLon,
            snappedEastM: best.sx,
            snappedNorthM: best.sy,
            crossTrackErrorM: best.crossDist,
            alongTrackDistanceM: best.alongDist,
            roadHeadingDeg: best.seg.headingDeg,
            headingDivergenceDeg: headingDiv,
            matchConfidence: confidence,
            isAmbiguous: isAmbiguous,
            candidateCount: scored.count,
            alternativeSegments: alternatives
        )
    }

    public static func fromJsonData(_ data: Data) throws -> RoadGraphPack {
        guard let root = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw NSError(domain: "RoadGraphPack", code: 1, userInfo: [NSLocalizedDescriptionKey: "Invalid JSON"])
        }
        return try fromDictionary(root)
    }

    public static func fromJsonString(_ jsonStr: String) throws -> RoadGraphPack {
        guard let data = jsonStr.data(using: .utf8) else {
            throw NSError(domain: "RoadGraphPack", code: 2, userInfo: [NSLocalizedDescriptionKey: "Invalid encoding"])
        }
        return try fromJsonData(data)
    }

    public static func fromDictionary(_ root: [String: Any]) throws -> RoadGraphPack {
        let name = (root["name"] as? String) ?? "road_pack"
        let cellSizeM = (root["cell_size_m"] as? NSNumber)?.doubleValue ?? 100.0
        guard let originLat = (root["origin_lat"] as? NSNumber)?.doubleValue,
              let originLon = (root["origin_lon"] as? NSNumber)?.doubleValue else {
            throw NSError(domain: "RoadGraphPack", code: 3, userInfo: [NSLocalizedDescriptionKey: "Missing origin_lat or origin_lon"])
        }

        var nodesMap: [String: RoadNode] = [:]
        if let nodesArr = root["nodes"] as? [[String: Any]] {
            for obj in nodesArr {
                guard let id = obj["id"] as? String,
                      let lat = (obj["lat"] as? NSNumber)?.doubleValue,
                      let lon = (obj["lon"] as? NSNumber)?.doubleValue else { continue }
                let eastM = (obj["east_m"] as? NSNumber)?.doubleValue ?? 0.0
                let northM = (obj["north_m"] as? NSNumber)?.doubleValue ?? 0.0
                nodesMap[id] = RoadNode(id: id, lat: lat, lon: lon, eastM: eastM, northM: northM)
            }
        }

        var segmentsMap: [String: RoadSegment] = [:]
        if let segsArr = root["segments"] as? [[String: Any]] {
            for obj in segsArr {
                guard let id = obj["id"] as? String,
                      let fromNodeId = obj["from_node"] as? String,
                      let toNodeId = obj["to_node"] as? String,
                      let fromNode = nodesMap[fromNodeId],
                      let toNode = nodesMap[toNodeId] else { continue }

                let headingDeg = (obj["heading_deg"] as? NSNumber)?.doubleValue ?? 0.0
                let calculatedLength = hypot(toNode.eastM - fromNode.eastM, toNode.northM - fromNode.northM)
                let lengthM = (obj["length_m"] as? NSNumber)?.doubleValue ?? calculatedLength
                let speedLimitMps = (obj["speed_limit_mps"] as? NSNumber)?.doubleValue ?? 20.0
                let laneCount = (obj["lane_count"] as? NSNumber)?.intValue ?? 1
                let roadType = (obj["road_type"] as? String) ?? "primary"
                let oneWay = (obj["one_way"] as? Bool) ?? false

                segmentsMap[id] = RoadSegment(
                    id: id,
                    fromNode: fromNodeId,
                    toNode: toNodeId,
                    startEastM: fromNode.eastM,
                    startNorthM: fromNode.northM,
                    endEastM: toNode.eastM,
                    endNorthM: toNode.northM,
                    headingDeg: headingDeg,
                    lengthM: lengthM,
                    speedLimitMps: speedLimitMps,
                    laneCount: laneCount,
                    roadType: roadType,
                    oneWay: oneWay
                )
            }
        }

        return RoadGraphPack(
            name: name,
            cellSizeM: cellSizeM,
            originLat: originLat,
            originLon: originLon,
            nodes: nodesMap,
            segments: segmentsMap
        )
    }
}
