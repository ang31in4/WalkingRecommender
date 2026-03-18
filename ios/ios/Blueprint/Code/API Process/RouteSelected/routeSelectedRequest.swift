import Foundation

/// Backend expects: user_id + route feature scores.
struct RouteSelectedPostBody: Encodable {
    let user_id: String
    let a_score: Double?
    let u_score: Double?
    let d_score: Double?
    let s_score: Double?
}

func postRouteSelected(userId: String, route: Route) async throws {
    let body = RouteSelectedPostBody(
        user_id: userId,
        a_score: route.accessibilityScore,
        u_score: route.urbanScore,
        d_score: route.difficultyScore,
        s_score: route.safetyScore
    )
    let endpoint = APIEndpoints.postRouteSelected

    guard let url = URL(string: endpoint.urlString) else {
        throw NSError(domain: "RouteSelected", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid URL"])
    }
    var request = URLRequest(url: url)
    request.httpMethod = endpoint.method.rawValue
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    request.httpBody = try JSONEncoder().encode(body)

    let (_, response) = try await URLSession.shared.data(for: request)
    guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
        throw NSError(domain: "RouteSelected", code: -1, userInfo: [NSLocalizedDescriptionKey: "Failed to save route selection"])
    }
}
