import Foundation

struct UserStepGoalResponse: Decodable {
    let success: Bool
    let user_id: String?
    let step_goal: Int?
    let current_step: Int?
    let error: String?
}

func getUserStepGoal(userId: String) async throws -> UserStepGoalResponse {
    let endpoint = APIEndpoints.getUserStepGoal(userId: userId)
    guard let url = URL(string: endpoint.urlString) else {
        throw NSError(domain: "UserStepGoal", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid URL"])
    }

    var request = URLRequest(url: url)
    request.httpMethod = endpoint.method.rawValue

    let (data, response) = try await URLSession.shared.data(for: request)
    guard let http = response as? HTTPURLResponse else {
        throw NSError(domain: "UserStepGoal", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid response"])
    }

    guard http.statusCode == 200 else {
        throw NSError(domain: "UserStepGoal", code: -1, userInfo: [NSLocalizedDescriptionKey: "Failed to fetch step_goal"])
    }

    let decoded = try JSONDecoder().decode(UserStepGoalResponse.self, from: data)
    guard decoded.success else {
        throw NSError(domain: "UserStepGoal", code: -1, userInfo: [NSLocalizedDescriptionKey: decoded.error ?? "Unknown error"])
    }

    return decoded
}

