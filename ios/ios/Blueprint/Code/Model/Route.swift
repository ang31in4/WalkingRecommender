import Foundation
import CoreLocation
import MapKit

struct Route: Identifiable, Decodable {
    let id: String
    let name: String
    let difficulty: String
    let coordinates: [CLLocationCoordinate2D]
    let length: Double
    let petFriendly: Bool?
    let wheelchairAccessible: Bool?
    let urban: Bool?
    let accessibilityScore: Double?
    let urbanScore: Double?
    let difficultyScore: Double?
    let safetyScore: Double?

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
        case a_score = "a_score"
        case u_score = "u_score"
        case d_score = "d_score"
        case s_score = "s_score"
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
        self.petFriendly = try propertiesContainer.decodeIfPresent(Bool.self, forKey: .pet_friendly)
        self.wheelchairAccessible = try propertiesContainer.decodeIfPresent(Bool.self, forKey: .wheelchair_accessible)
        self.urban = try propertiesContainer.decodeIfPresent(Bool.self, forKey: .urban)
        self.accessibilityScore = try propertiesContainer.decodeIfPresent(Double.self, forKey: .a_score)
        self.urbanScore = try propertiesContainer.decodeIfPresent(Double.self, forKey: .u_score)
        self.difficultyScore = try propertiesContainer.decodeIfPresent(Double.self, forKey: .d_score)
        self.safetyScore = try propertiesContainer.decodeIfPresent(Double.self, forKey: .s_score)
        self.id = UUID().uuidString
    }

    /// For previews and testing without the backend.
    init(
        id: String = UUID().uuidString,
        name: String,
        difficulty: String = "moderate",
        coordinates: [CLLocationCoordinate2D],
        length: Double,
        petFriendly: Bool? = nil,
        wheelchairAccessible: Bool? = nil,
        urban: Bool? = nil,
        accessibilityScore: Double? = nil,
        urbanScore: Double? = nil,
        difficultyScore: Double? = nil,
        safetyScore: Double? = nil
    ) {
        self.id = id
        self.name = name
        self.difficulty = difficulty
        self.coordinates = coordinates
        self.length = length
        self.petFriendly = petFriendly
        self.wheelchairAccessible = wheelchairAccessible
        self.urban = urban
        self.accessibilityScore = accessibilityScore
        self.urbanScore = urbanScore
        self.difficultyScore = difficultyScore
        self.safetyScore = safetyScore
    }

    /// Sample route for previews (e.g. MapView without backend).
    static var sample: Route {
        let coords: [CLLocationCoordinate2D] = [
            CLLocationCoordinate2D(latitude: 33.6405, longitude: -117.8443),
            CLLocationCoordinate2D(latitude: 33.6410, longitude: -117.8438),
            CLLocationCoordinate2D(latitude: 33.6415, longitude: -117.8430),
            CLLocationCoordinate2D(latitude: 33.6420, longitude: -117.8425),
            CLLocationCoordinate2D(latitude: 33.6425, longitude: -117.8420),
        ]
        return Route(
            name: "Sample Loop (1.2 mi)",
            difficulty: "moderate",
            coordinates: coords,
            length: 1.2,
            petFriendly: true,
            urban: true
        )
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
