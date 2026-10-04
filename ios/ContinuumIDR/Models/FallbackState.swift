import Foundation
import SwiftUI

public enum FallbackState: String, CaseIterable, Codable {
    case gnssHealthy = "GNSS_HEALTHY"
    case outagePending = "OUTAGE_PENDING"
    case fallbackActive = "FALLBACK_ACTIVE"
    case recovering = "RECOVERING"

    public var title: String {
        switch self {
        case .gnssHealthy:
            return "● GNSS LOCKED (ACTIVE)"
        case .outagePending:
            return "● SIGNAL DEGRADED / OUTAGE PENDING"
        case .fallbackActive:
            return "● INERTIAL DEAD RECKONING (FALLBACK ACTIVE)"
        case .recovering:
            return "● RE-CONVERGING GNSS"
        }
    }

    public var badgeColor: Color {
        switch self {
        case .gnssHealthy:
            return Color(red: 0.02, green: 0.59, blue: 0.41) // Emerald Green
        case .outagePending:
            return Color(red: 0.85, green: 0.47, blue: 0.02) // Amber
        case .fallbackActive:
            return Color(red: 0.86, green: 0.15, blue: 0.15) // Crimson Red
        case .recovering:
            return Color(red: 0.85, green: 0.47, blue: 0.02) // Amber
        }
    }
}
