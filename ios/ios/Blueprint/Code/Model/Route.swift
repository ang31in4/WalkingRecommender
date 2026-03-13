import Foundation
import CoreLocation
import MapKit

struct Route: Identifiable, Decodable {
    let id: String
    let name: String
    let difficulty: String
    let coordinates: [CLLocationCoordinate2D]
    let length: Double
    
    enum CodingKeys: String, CodingKey {
        case geometry
        case properties
    }
    
    enum GeometryKeys: String, CodingKey {
        case coordinates
    }
    
    enum PropertyKeys: String, CodingKey {
        case name
        case lengthMiles = "length_mi"
        case lengthMeters = "length_m"
        case distanceM = "distance_m"
        case pet_friendly = "pet_friendly"
        case wheelchair_accessible = "wheelchair_accessible"
        case urban = "urban"
        case difficulty = "difficulty"
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: Route.CodingKeys.self)
        let geometryContainer = try container.nestedContainer(keyedBy: GeometryKeys.self, forKey: .geometry)
        let coordinates = try geometryContainer.decode([[Double]].self, forKey: .coordinates)
        let propertiesContainer = try container.nestedContainer(keyedBy: PropertyKeys.self, forKey: .properties)
        
        self.coordinates = coordinates.map {
            coord in
            CLLocationCoordinate2D(latitude: coord[1], longitude: coord[0])
        }
        
        self.name = try propertiesContainer.decodeIfPresent(String.self, forKey: .name) ?? "Route"
        if let mi = try propertiesContainer.decodeIfPresent(Double.self, forKey: .lengthMiles) {
            self.length = mi
        } else if let m = try propertiesContainer.decodeIfPresent(Double.self, forKey: .distanceM) {
            self.length = m / 1609.34
        } else {
            self.length = 0
        }
        self.difficulty = try propertiesContainer.decodeIfPresent(String.self, forKey: .difficulty) ?? "moderate"
        self.id = UUID().uuidString
    }
}

extension Route {
    func distanceFromStart(from userLocation: CLLocation) -> Double? {
        guard let firstCoordinate = coordinates.first else { return nil }
        let startLocation = CLLocation(latitude: firstCoordinate.latitude, longitude: firstCoordinate.longitude)
        return userLocation.distance(from: startLocation)
    }
    
    func asPolyline() -> MKPolyline {
        MKPolyline(coordinates: coordinates, count: coordinates.count)
    }
}
