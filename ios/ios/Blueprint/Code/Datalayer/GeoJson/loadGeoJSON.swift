import MapKit

struct PolygonInfo: Decodable {
    let type: String?
    let geometry : String?
    let properties: Data?
}

struct Geometry: Decodable {
    let type: String?
    let coordinates: [[Double]]?
}

struct Properties: Decodable {
    let length_mile: Int
    let length_m: Int
    let count: Int
}

func loadGeoJson() {
    guard let url = Bundle.main.url(forResource: "SampleGeoJson", withExtension: "geojson") else {
        print("Error: file not found in Bundle")
        return
    }
    var geoJson = [MKGeoJSONObject]()
    var overlays = [MKOverlay]()
    
    do {
        let data = try Data(contentsOf: url)
        geoJson = try MKGeoJSONDecoder().decode(data)
    } catch {
        fatalError("Unable to decode Json")
    }
    
    for item in geoJson {
        if let feature = item as? MKGeoJSONFeature {
            let geometry = feature.geometry
            var polygonInfo: PolygonInfo? = nil
            
            if let propertiesData = feature.properties {
                polygonInfo = try? JSONDecoder.init().decode(PolygonInfo.self, from: propertiesData)
            }
            
            for geo in feature.geometry {
                if let polygon = geo as? MKPolyline {
                    overlays.append(polygon)
                }
            }
        }
    }
}

