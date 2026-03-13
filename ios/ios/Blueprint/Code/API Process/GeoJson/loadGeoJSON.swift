import Foundation
import CoreLocation

func loadGeoJsonFromAPI(
    latitude: Double,
    longitude: Double,
) async -> [Route] {
    let endpoint = APIEndpoints.getRoutes
    guard let url = URL(string: endpoint.urlString) else {
        print("API load failed: Invalid URL")
        return []
    }
    
    var request = URLRequest(url: url)
        request.httpMethod = endpoint.method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

    if let sessionToken = UserDefaults.standard.string(forKey: "sessionToken") {
            request.setValue("Bearer \(sessionToken)", forHTTPHeaderField: "Authorization")
        } else {
            print("API load failed: No session token found")
            return []
        }

    do {
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            let code = (response as? HTTPURLResponse)?.statusCode ?? -1
            print("API load failed: HTTP \(code)")
            return []
        }
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let type = json["type"] as? String,
              type == "FeatureCollection",
              let features = json["features"] as? [[String: Any]] else {
            print("API load failed: response is not FeatureCollection or missing features")
            return []
        }
        
        // Decode routes off the main actor so UI stays responsive
        let routes = await Task.detached(priority: .userInitiated) {
            let decoder = JSONDecoder()
            var result: [Route] = []
            for (i, feature) in features.enumerated() {
                guard let featureData = try? JSONSerialization.data(withJSONObject: feature),
                      let route = try? decoder.decode(Route.self, from: featureData) else {
                    print("API load: failed to decode feature at index \(i)")
                    continue
                }
                result.append(route)
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
