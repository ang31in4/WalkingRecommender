import Foundation
import CoreLocation

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

