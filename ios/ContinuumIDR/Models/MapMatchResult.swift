import Foundation

public struct RoadNode: Codable {
    public let id: String
    public let lat: Double
    public let lon: Double
    public let eastM: Double
    public let northM: Double

    public init(id: String, lat: Double, lon: Double, eastM: Double = 0.0, northM: Double = 0.0) {
        self.id = id
        self.lat = lat
        self.lon = lon
        self.eastM = eastM
        self.northM = northM
    }
}

public struct RoadSegment: Codable {
    public let id: String
    public let fromNode: String
    public let toNode: String
    public let startEastM: Double
    public let startNorthM: Double
    public let endEastM: Double
    public let endNorthM: Double
    public let headingDeg: Double
    public let lengthM: Double
    public let speedLimitMps: Double
    public let laneCount: Int
    public let roadType: String
    public let oneWay: BooleanLiteralType

    public init(
        id: String,
        fromNode: String,
        toNode: String,
        startEastM: Double,
        startNorthM: Double,
        endEastM: Double,
        endNorthM: Double,
        headingDeg: Double = 0.0,
        lengthM: Double = 0.0,
        speedLimitMps: Double = 20.0,
        laneCount: Int = 1,
        roadType: String = "primary",
        oneWay: Bool = false
    ) {
        self.id = id
        self.fromNode = fromNode
        self.toNode = toNode
        self.startEastM = startEastM
        self.startNorthM = startNorthM
        self.endEastM = endEastM
        self.endNorthM = endNorthM
        self.headingDeg = headingDeg
        self.lengthM = lengthM
        self.speedLimitMps = speedLimitMps
        self.laneCount = laneCount
        self.roadType = roadType
        self.oneWay = oneWay
    }
}

public struct MapMatchResult: Codable {
    public let matched: Bool
    public let segmentId: String?
    public let snappedLat: Double?
    public let snappedLon: Double?
    public let snappedEastM: Double?
    public let snappedNorthM: Double?
    public let crossTrackErrorM: Double
    public let alongTrackDistanceM: Double
    public let roadHeadingDeg: Double?
    public let headingDivergenceDeg: Double?
    public let matchConfidence: Double
    public let isAmbiguous: Bool
    public let candidateCount: Int
    public let alternativeSegments: [String]

    public init(
        matched: Bool,
        segmentId: String? = nil,
        snappedLat: Double? = nil,
        snappedLon: Double? = nil,
        snappedEastM: Double? = nil,
        snappedNorthM: Double? = nil,
        crossTrackErrorM: Double = .nan,
        alongTrackDistanceM: Double = .nan,
        roadHeadingDeg: Double? = nil,
        headingDivergenceDeg: Double? = nil,
        matchConfidence: Double = 0.0,
        isAmbiguous: Bool = false,
        candidateCount: Int = 0,
        alternativeSegments: [String] = []
    ) {
        self.matched = matched
        self.segmentId = segmentId
        self.snappedLat = snappedLat
        self.snappedLon = snappedLon
        self.snappedEastM = snappedEastM
        self.snappedNorthM = snappedNorthM
        self.crossTrackErrorM = crossTrackErrorM
        self.alongTrackDistanceM = alongTrackDistanceM
        self.roadHeadingDeg = roadHeadingDeg
        self.headingDivergenceDeg = headingDivergenceDeg
        self.matchConfidence = matchConfidence
        self.isAmbiguous = isAmbiguous
        self.candidateCount = candidateCount
        self.alternativeSegments = alternativeSegments
    }
}
