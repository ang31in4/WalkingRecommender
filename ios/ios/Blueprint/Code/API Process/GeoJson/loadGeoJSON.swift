import Foundation
import CoreLocation

func loadGeoJsonFromAPI(
    latitude: Double,
    longitude: Double,
    userId: String? = nil
) async -> [Route] {
    let endpoint = APIEndpoints.getRoutes
    guard let url = URL(string: endpoint.urlString) else {
        print("API load failed: Invalid URL")
        return []
    }

    var body: [String: Any] = [
        "latitude": latitude,
        "longitude": longitude,
    ]
    if let uid = userId, !uid.isEmpty {
        body["user_id"] = uid
    }

    var request = URLRequest(url: url)
    request.httpMethod = endpoint.method.rawValue
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    guard let bodyData = try? JSONSerialization.data(withJSONObject: body) else {
        print("API load failed: Could not encode request body")
        return []
    }
    request.httpBody = bodyData

    do {
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            let code = (response as? HTTPURLResponse)?.statusCode ?? -1
            print("API load failed: HTTP \(code)")
            return []
        }
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let type = json["type"] as? String,
              type == "FeatureCollection" else {
            print("API load failed: response is not FeatureCollection")
            return []
        }
        let features = json["features"] as? [[String: Any]] ?? []
        if features.isEmpty {
            print("API load: backend returned 0 features (check location has graph data)")
            return []
        }

        let routes = await Task.detached(priority: .userInitiated) {
            let decoder = JSONDecoder()
            var result: [Route] = []
            for (i, feature) in features.enumerated() {
                guard let featureData = try? JSONSerialization.data(withJSONObject: feature) else {
                    print("API load: failed to serialize feature at index \(i)")
                    continue
                }
                do {
                    let route = try decoder.decode(Route.self, from: featureData)
                    result.append(route)
                } catch {
                    print("API load: decode failed at index \(i): \(error)")
                }
            }
            return result
        }.value
        
        if !routes.isEmpty {
            print("Loaded \(routes.count) routes from API")
        }
        
        return routes
    } catch {
        print("API load failed: \(error)")
        return []
    }
}
