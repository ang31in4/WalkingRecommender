import Foundation
import SwiftUI

struct FilterModel {
    var selectedDifficulty: RouteDifficulty?
    var selectedDistance: DistanceRange?
    var selectedSuitability: Set<Suitability> = []

    mutating func clear() {
        selectedDifficulty = nil
        selectedDistance = nil
        selectedSuitability.removeAll()
    }

    /// True when no filters are applied (shows all routes)
    var isDefault: Bool {
        selectedDifficulty == nil && selectedDistance == nil && selectedSuitability.isEmpty
    }
}

enum RouteDifficulty: String, CaseIterable {
    case easy
    case moderate
    case hard

    var displayName: String {
        rawValue.capitalized
    }
}

enum DistanceRange: String, CaseIterable {
    case lessThanHalfMile = "less_than_0.5_mile"
    case fromHalfTo1Mile = "from_0.5_to_1_mile"
    case greaterThan1Mile = "greater_than_1_mile"

    var displayName: String {
        switch self {
        case .lessThanHalfMile: return "Less than 0.5 mile"
        case .fromHalfTo1Mile: return "From 0.5 to 1 mile"
        case .greaterThan1Mile: return "Greater than 1 mile"
        }
    }

    /// Returns (minDistanceM, maxDistanceM) for API. Uses 1000–2000 m when nil.
    static func minMaxMeters(for distance: DistanceRange?) -> (min: Double, max: Double) {
        let metersPerMile = 1609.34
        guard let dist = distance else { return (1000, 2000) }
        switch dist {
        case .lessThanHalfMile: return (100, 0.5 * metersPerMile)
        case .fromHalfTo1Mile: return (0.5 * metersPerMile, 1.0 * metersPerMile)
        case .greaterThan1Mile: return (1.0 * metersPerMile, 5000)
        }
    }
}

enum Suitability: String, CaseIterable {
    case petFriendly = "pet_friendly"
    case wheelchairAccessible = "wheelchair_accessible"
    case strollerFriendly = "stroller_friendly"

    var displayName: String {
        switch self {
        case .petFriendly: return "Pet Friendly"
        case .wheelchairAccessible: return "Wheelchair-friendly"
        case .strollerFriendly: return "Stroller-friendly"
        }
    }
}
