import Foundation

public struct TrafficHazardReport: Identifiable, Codable {
    public var id: String { "\(hazardType)_\(timestampMs)_\(vehicleId)" }
    public let hazardType: String
    public let severity: Double
    public let latitude: Double
    public let longitude: Double
    public let timestampMs: Int64
    public let vehicleId: String

    public init(
        hazardType: String,
        severity: Double,
        latitude: Double,
        longitude: Double,
        timestampMs: Int64,
        vehicleId: String
    ) {
        self.hazardType = hazardType
        self.severity = severity
        self.latitude = latitude
        self.longitude = longitude
        self.timestampMs = timestampMs
        self.vehicleId = vehicleId
    }
}

public struct BleRelayStats: Codable {
    public var sentCount: Int64
    public var receivedCount: Int64
    public var relayedCount: Int64
    public var duplicateCount: Int64
    public var expiredCount: Int64

    public init(
        sentCount: Int64 = 0,
        receivedCount: Int64 = 0,
        relayedCount: Int64 = 0,
        duplicateCount: Int64 = 0,
        expiredCount: Int64 = 0
    ) {
        self.sentCount = sentCount
        self.receivedCount = receivedCount
        self.relayedCount = relayedCount
        self.duplicateCount = duplicateCount
        self.expiredCount = expiredCount
    }
}
