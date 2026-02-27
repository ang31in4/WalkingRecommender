import Foundation
import SwiftUI

struct FilterModel {
    var selectedDifficulty: RouteDifficulty = .easy
    var selectedDistance: DistanceRange = .lessThanHalfMile
    var selectedSuitability: Set<Suitability> = []

    mutating func clear() {
        selectedDifficulty = .easy
        selectedDistance = .lessThanHalfMile
        selectedSuitability.removeAll()
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
