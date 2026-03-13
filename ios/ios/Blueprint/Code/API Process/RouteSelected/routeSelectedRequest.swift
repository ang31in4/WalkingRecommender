import Foundation

/// Backend expects: user_id (route choice is recorded with zero scores).
struct RouteSelectedPostBody: Encodable {
    let user_id: String
}

func postRouteSelected(userId: String, route: Route) async throws {
    let body = RouteSelectedPostBody(user_id: userId)
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
