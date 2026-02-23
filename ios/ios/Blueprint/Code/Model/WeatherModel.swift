import Foundation
import Combine

struct WeatherResponse: Codable {
    let current: Current
    let hourly: [Hourly] //48 hours
}

struct Current: Codable {
    let temp: Double
    let pressure: Int
    let humidity: Int
    let uvi: Double
    let weather: [Weather]
    let wind_speed: Double
    let rain: Rain?
}

struct Weather: Codable {
    let main: String
    let icon: String
}

struct Hourly: Codable {
    let wind_speed: Double
    let temp: Double
    let weather: [Weather]
    let uvi: Double
    let rain: Rain?
}

struct Rain : Codable {
    enum CodingKeys: String, CodingKey {
            case oneHour = "1h"
        }
    let oneHour: Double?
}
