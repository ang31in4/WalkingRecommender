import Foundation

/// Backend expects: difficulty ("easy"|"moderate"|"difficult"), distance (string), wheelchair_access, avoid_steps, pet_friendly, urban.
struct FiltersPostBody: Encodable {
    let user_id: String
    let difficulty: String?
    let distance: String?
    let wheelchair_access: Bool
//    let avoid_steps: Bool
    let pet_friendly: Bool
    let urban: Bool
}

//{
//  "user_id": "user_123",
//  "difficulty": null,
//  "distance": null,
//  "wheelchair_access": false,
//  "pet_friendly": false,
//  "urban": false
//}

/// Maps FilterModel to backend format and POSTs to /api/filters so get_last_filters_for_user returns these on next login.
func postFilters(userId: String, filter: FilterModel) async throws {
    let difficulty: String? = {
        guard let d = filter.selectedDifficulty else { return nil }
        return d == .hard ? "difficult" : d.rawValue
    }()
    let distance: String? = filter.selectedDistance?.rawValue
    let wheelchair_access = filter.selectedSuitability.contains(.wheelchairAccessible)
    let pet_friendly = filter.selectedSuitability.contains(.petFriendly)
    let urban = filter.selectedSuitability.contains(.urban)

    let body = FiltersPostBody(
        user_id: userId,
        difficulty: difficulty,
        distance: distance,
        wheelchair_access: wheelchair_access,
//        avoid_steps: false,
        pet_friendly: pet_friendly,
        urban: urban
    )

    guard let url = URL(string: "\(APIConfig.baseURL)/api/filters") else {
        throw NSError(domain: "Filters", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid URL"])
    }
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    request.httpBody = try JSONEncoder().encode(body)

    let (_, response) = try await URLSession.shared.data(for: request)
    guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
        throw NSError(domain: "Filters", code: -1, userInfo: [NSLocalizedDescriptionKey: "Failed to save filters"])
    }
}
