import Foundation

public enum VehicleProfile: String, CaseIterable, Identifiable, Codable {
    case car = "CAR"
    case motorcycle = "MOTORCYCLE"
    case parking = "PARKING"
    case externalImu = "EXTERNAL_IMU"

    public var id: String { rawValue }

    public var displayName: String {
        switch self {
        case .car: return "Passenger Car"
        case .motorcycle: return "Motorcycle (Lean Aware)"
        case .parking: return "Basement Parking / Crawl"
        case .externalImu: return "External High-Rate IMU"
        }
    }
}
