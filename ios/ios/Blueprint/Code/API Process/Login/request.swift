import Foundation

struct LoginRequest: Encodable {
    let user_id: String
}

struct LoginResponse: Decodable {
    let success: Bool
    let user_id: String?
    let error: String?
}

func loginRequest(userId: String) async throws -> Bool {
    guard let url = URL(string: "\(APIConfig.baseURL)/api/login") else {
        throw NSError(domain: "Login", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid URL"])
    }

    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")

    let body = LoginRequest(user_id: userId)
    request.httpBody = try JSONEncoder().encode(body)

    let (data, response) = try await URLSession.shared.data(for: request)

    guard let httpResponse = response as? HTTPURLResponse else {
        throw NSError(domain: "Login", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid response"])
    }

    let decoded = try JSONDecoder().decode(LoginResponse.self, from: data)

    if httpResponse.statusCode == 200 && decoded.success {
        return true
    }
    return false
}
