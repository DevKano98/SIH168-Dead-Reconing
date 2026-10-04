import Foundation

public struct EngineDiagnostics: Codable {
    public var imuSamplesCount: Int64
    public var gnssFixesCount: Int64
    public var deadReckonStepsCount: Int64
    public var lastInferenceLatencyUs: Int64
    public var avgInferenceLatencyUs: Int64
    public var lastMapMatchLatencyUs: Int64
    public var avgMapMatchLatencyUs: Int64
    public var estimatedMemoryKb: Int64
    public var currentProfile: String
    public var currentState: String

    public init(
        imuSamplesCount: Int64 = 0,
        gnssFixesCount: Int64 = 0,
        deadReckonStepsCount: Int64 = 0,
        lastInferenceLatencyUs: Int64 = 0,
        avgInferenceLatencyUs: Int64 = 0,
        lastMapMatchLatencyUs: Int64 = 0,
        avgMapMatchLatencyUs: Int64 = 0,
        estimatedMemoryKb: Int64 = 0,
        currentProfile: String = "CAR",
        currentState: String = "GNSS_HEALTHY"
    ) {
        self.imuSamplesCount = imuSamplesCount
        self.gnssFixesCount = gnssFixesCount
        self.deadReckonStepsCount = deadReckonStepsCount
        self.lastInferenceLatencyUs = lastInferenceLatencyUs
        self.avgInferenceLatencyUs = avgInferenceLatencyUs
        self.lastMapMatchLatencyUs = lastMapMatchLatencyUs
        self.avgMapMatchLatencyUs = avgMapMatchLatencyUs
        self.estimatedMemoryKb = estimatedMemoryKb
        self.currentProfile = currentProfile
        self.currentState = currentState
    }
}
