import Foundation

struct UserStepsPostBody: Encodable {
    let current_steps: Int
}

func postUserSteps(userId: String, currentSteps: Int) async throws {
    let endpoint = APIEndpoints.postUserSteps(userId: userId)
    guard let url = URL(string: endpoint.urlString) else {
        throw NSError(domain: "UserSteps", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid URL"])
    }
    var request = URLRequest(url: url)
    request.httpMethod = endpoint.method.rawValue
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    request.httpBody = try JSONEncoder().encode(UserStepsPostBody(current_steps: max(0, currentSteps)))

    let (_, response) = try await URLSession.shared.data(for: request)
    guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
        throw NSError(domain: "UserSteps", code: -1, userInfo: [NSLocalizedDescriptionKey: "Failed to update steps"])
    }
}
