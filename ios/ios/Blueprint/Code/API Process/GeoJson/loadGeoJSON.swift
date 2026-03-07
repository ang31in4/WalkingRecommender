import Foundation
import CoreLocation

func filterRoutes(_ routes: [Route], by filter: FilterModel) -> [Route] {
    guard !filter.isDefault else { return routes }

    return routes.filter { route in
        let matchesDifficulty: Bool = {
            guard let diff = filter.selectedDifficulty else { return true }
            return route.difficulty.lowercased() == diff.rawValue.lowercased()
        }()
        let matchesDistance: Bool = {
            guard let dist = filter.selectedDistance else { return true }
            let miles = route.length
            switch dist {
            case .lessThanHalfMile: return miles < 0.5
            case .fromHalfTo1Mile: return miles >= 0.5 && miles <= 1.0
            case .greaterThan1Mile: return miles > 1.0
            }
        }()
        return matchesDifficulty && matchesDistance
    }
}

func loadGeoJson() -> [Route] {
    guard let url = Bundle.main.url(forResource: "SampleGeoJson", withExtension: "geojson") else {
        print("Error: file not found in Bundle")
        return []
    }

    guard let data = try? Data(contentsOf: url) else {
        print("Error: couldn't read file")
        return []
    }

    guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
          let type = json["type"] as? String else {
        return []
    }

    let decoder = JSONDecoder()
    if type == "Feature" {
        if let route = try? decoder.decode(Route.self, from: data) {
            return [route]
        }
    } else if type == "FeatureCollection",
              let features = json["features"] as? [[String: Any]] {
        return features.compactMap { feature in
            guard let featureData = try? JSONSerialization.data(withJSONObject: feature),
                  let route = try? decoder.decode(Route.self, from: featureData) else { return nil }
            return route
        }
    }

    return []
}

func loadGeoJsonFromAPI(
    latitude: Double,
    longitude: Double,
    minDistanceM: Double,
    maxDistanceM: Double,
    userId: String? = nil
) async -> [Route] {
    guard let url = URL(string: "\(APIConfig.baseURL)/api/routes") else { return [] }
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    request.timeoutInterval = 60

    var body: [String: Any] = [
        "latitude": latitude,
        "longitude": longitude,
        "min_distance_m": minDistanceM,
        "max_distance_m": maxDistanceM,
        "max_start_distance_m": 2000.0,
    ]
    if let uid = userId, !uid.isEmpty {
        body["user_id"] = uid
    }
    guard let bodyData = try? JSONSerialization.data(withJSONObject: body) else {
        print("API load failed: could not encode request body")
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
              type == "FeatureCollection",
              let features = json["features"] as? [[String: Any]] else {
            print("API load failed: response is not FeatureCollection or missing features")
            return []
        }
        let decoder = JSONDecoder()
        var routes: [Route] = []
        for (i, feature) in features.enumerated() {
            guard let featureData = try? JSONSerialization.data(withJSONObject: feature),
                  let route = try? decoder.decode(Route.self, from: featureData) else {
                print("API load: failed to decode feature at index \(i)")
                continue
            }
            routes.append(route)
        }
        if !routes.isEmpty {
            print("Loaded \(routes.count) routes from API")
        }
        return routes
    } catch {
        print("API load failed: \(error)")
        return []
    }
}
