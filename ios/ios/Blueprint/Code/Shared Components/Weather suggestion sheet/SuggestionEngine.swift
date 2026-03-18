import Foundation
import CoreLocation

enum SuggestionCategory {
    case health
    case clothing
    case safety
    case comfort
}

struct Suggestion {
    let id: String
    let category: SuggestionCategory
    let message: String
    let priority: Int
    let condition: (Context) -> Bool
}

struct Context {
    let route: Route
    let timeOfDay: Date
    let weather: WeatherData

    var temperature: Double { weather.temperature }
    var uvIndex: Int? { weather.uvIndex }
}

class SuggestionEngine {
    private let rules: [Suggestion] = [
        
        // ===== SUNNY CONDITIONS =====
        Suggestion(
            id: "sunscreen_high_uv",
            category: .health,
            message: "Sunscreen (SPF 30+)",
            priority: 1,
            condition: { context in
                guard let uv = context.uvIndex else { return false }
                return uv >= 6 && context.weather.condition.contains("sun")
            }
        ),
        Suggestion(
            id: "sunglasses",
            category: .clothing,
            message: "Sunglasses with UV protection",
            priority: 1,
            condition: { context in
                guard let uv = context.uvIndex else { return false }
                return uv >= 3 || context.weather.condition.contains("sun")
            }
        ),
        Suggestion(
            id: "wide_brim_hat",
            category: .clothing,
            message: "Wide-brim hat or cap",
            priority: 2,
            condition: { context in
                return context.weather.condition.contains("sun") || context.isMidday()
            }
        ),
        Suggestion(
            id: "light_clothing",
            category: .clothing,
            message: "Light-colored, breathable clothing",
            priority: 3,
            condition: { context in
                return context.weather.condition.contains("sun") && context.temperature > 75
            }
        ),
        Suggestion(
            id: "extra_water_hot",
            category: .health,
            message: "Bring water (hot weather)",
            priority: 1,
            condition: { context in
                // Hot weather: hydration matters even for shorter routes.
                return context.temperature > 80 ||
                       (context.temperature > 75 && context.route.length > 3.0)
            }
        ),
        Suggestion(
            id: "cooling_towel",
            category: .comfort,
            message: "Cooling towel or neck gaiter",
            priority: 4,
            condition: { context in
                return context.temperature > 85
            }
        ),
        Suggestion(
            id: "seek_shade",
            category: .safety,
            message: "Plan breaks in shaded areas",
            priority: 3,
            condition: { context in
                return context.temperature > 80 && context.route.length > 2.0
            }
        ),
        
        // ===== RAINY CONDITIONS =====
        Suggestion(
            id: "rain_jacket",
            category: .clothing,
            message: "Waterproof rain jacket",
            priority: 1,
            condition: { context in
                return context.weather.condition.contains("rain") ||
                       context.weather.precipitationChance > 0.5
            }
        ),
        Suggestion(
            id: "waterproof_pants",
            category: .clothing,
            message: "Waterproof or quick-dry pants",
            priority: 2,
            condition: { context in
                return context.weather.condition.contains("rain") &&
                       context.weather.precipitationChance > 0.7
            }
        ),
        Suggestion(
            id: "umbrella",
            category: .comfort,
            message: "Compact umbrella",
            priority: 3,
            condition: { context in
                return context.weather.precipitationChance > 0.3 &&
                       !context.weather.condition.contains("storm")
            }
        ),
        Suggestion(
            id: "waterproof_shoes",
            category: .clothing,
            message: "Waterproof hiking boots or shoes",
            priority: 1,
            condition: { context in
                return context.weather.condition.contains("rain") ||
                       context.weather.precipitationChance > 0.5
            }
        ),
        Suggestion(
            id: "dry_bag",
            category: .safety,
            message: "Waterproof bag for phone/valuables",
            priority: 2,
            condition: { context in
                return context.weather.precipitationChance > 0.4
            }
        ),
        Suggestion(
            id: "extra_socks",
            category: .comfort,
            message: "Extra pair of dry socks",
            priority: 3,
            condition: { context in
                return context.weather.condition.contains("rain") &&
                       context.route.length > 2.0
            }
        ),
        Suggestion(
            id: "avoid_trail_rain",
            category: .safety,
            message: "Watch for slippery surfaces and puddles",
            priority: 1,
            condition: { context in
                return context.weather.condition.contains("rain")
            }
        ),
        Suggestion(
            id: "towel_rain",
            category: .comfort,
            message: "Small towel to dry off",
            priority: 4,
            condition: { context in
                return context.weather.condition.contains("rain")
            }
        ),
        
        // ===== WINDY CONDITIONS =====
        Suggestion(
            id: "windbreaker",
            category: .clothing,
            message: "Windbreaker or wind-resistant jacket",
            priority: 1,
            condition: { context in
                return context.weather.windSpeed > 15
            }
        ),
        Suggestion(
            id: "secure_hat",
            category: .clothing,
            message: "Hat with chin strap or secure fit",
            priority: 2,
            condition: { context in
                return context.weather.windSpeed > 12
            }
        ),
        Suggestion(
            id: "eye_protection_wind",
            category: .safety,
            message: "Eye protection (dust/debris)",
            priority: 2,
            condition: { context in
                return context.weather.windSpeed > 20
            }
        ),
        Suggestion(
            id: "layers_wind",
            category: .clothing,
            message: "Extra layers - wind chill is colder",
            priority: 1,
            condition: { context in
                return context.weather.windSpeed > 15 && context.temperature < 60
            }
        ),
        Suggestion(
            id: "secure_items",
            category: .safety,
            message: "Secure loose items in backpack",
            priority: 3,
            condition: { context in
                return context.weather.windSpeed > 18
            }
        ),
        Suggestion(
            id: "avoid_exposed_wind",
            category: .safety,
            message: "Consider sheltered routes if possible",
            priority: 2,
            condition: { context in
                return context.weather.windSpeed > 25
            }
        ),
        Suggestion(
            id: "lip_balm_wind",
            category: .comfort,
            message: "Lip balm (wind can dry lips)",
            priority: 4,
            condition: { context in
                return context.weather.windSpeed > 15
            }
        ),
        
        // ===== CLOUDY CONDITIONS =====
        Suggestion(
            id: "sunscreen_cloudy",
            category: .health,
            message: "Sunscreen (UV rays penetrate clouds)",
            priority: 2,
            condition: { context in
                guard let uv = context.uvIndex else { return false }
                return uv >= 3 && context.weather.condition.contains("cloud")
            }
        ),
        Suggestion(
            id: "light_jacket_cloudy",
            category: .clothing,
            message: "Light jacket (temperature may drop)",
            priority: 2,
            condition: { context in
                return context.weather.condition.contains("cloud") &&
                       context.temperature < 70
            }
        ),
        Suggestion(
            id: "check_forecast",
            category: .safety,
            message: "Check forecast - clouds may bring rain",
            priority: 3,
            condition: { context in
                return context.weather.condition.contains("cloud") &&
                       context.weather.precipitationChance > 0.2
            }
        ),
        
        // ===== LOW HUMIDITY CONDITIONS =====
        Suggestion(
            id: "extra_water_dry",
            category: .health,
            message: "Extra water - dry air increases dehydration",
            priority: 1,
            condition: { context in
                return context.weather.humidity < 30
            }
        ),
        Suggestion(
            id: "moisturizer",
            category: .comfort,
            message: "Moisturizer or lotion for dry skin",
            priority: 3,
            condition: { context in
                return context.weather.humidity < 25
            }
        ),
        Suggestion(
            id: "lip_balm_dry",
            category: .comfort,
            message: "Lip balm with SPF",
            priority: 3,
            condition: { context in
                return context.weather.humidity < 30
            }
        ),
        Suggestion(
            id: "nasal_spray",
            category: .health,
            message: "Saline nasal spray (for dry sinuses)",
            priority: 4,
            condition: { context in
                return context.weather.humidity < 20
            }
        ),
        Suggestion(
            id: "eye_drops",
            category: .comfort,
            message: "Eye drops (dry air irritates eyes)",
            priority: 4,
            condition: { context in
                return context.weather.humidity < 25
            }
        ),
        
        // ===== GENERAL CONDITIONS =====
        Suggestion(
            id: "cold_scarf_coat",
            category: .clothing,
            message: "Scarf and coat (cold weather)",
            priority: 1,
            condition: { context in
                // Cold weather: add a warm layer regardless of route/difficulty.
                return context.temperature < 55
            }
        ),
        Suggestion(
            id: "water_base",
            category: .health,
            message: "Water",
            priority: 1,
            condition: { context in
                return context.route.length > 1.0
            }
        ),
        Suggestion(
            id: "snacks",
            category: .health,
            message: "Energy snacks (trail mix, granola bars)",
            priority: 3,
            condition: { context in
                return context.route.length > 3.0
            }
        ),
        Suggestion(
            id: "first_aid",
            category: .safety,
            message: "Small first-aid kit (bandages, pain relief)",
            priority: 4,
            condition: { context in
                return context.route.length > 5.0
            }
        ),
        Suggestion(
            id: "phone_battery",
            category: .safety,
            message: "Fully charged phone or power bank",
            priority: 2,
            condition: { context in
                return context.route.length > 4.0
            }
        ),
        Suggestion(
            id: "flashlight_dusk",
            category: .safety,
            message: "Flashlight or headlamp",
            priority: 2,
            condition: { context in
                return context.isDusk() || context.isEarlyMorning()
            }
        ),
        Suggestion(
            id: "insect_repellent",
            category: .comfort,
            message: "Insect repellent",
            priority: 3,
            condition: { context in
                return context.temperature > 65 &&
                       (context.isEarlyMorning() || context.isDusk()) &&
                       context.weather.humidity > 60
            }
        ),
        Suggestion(
            id: "proper_footwear",
            category: .safety,
            message: "Proper walking/hiking shoes",
            priority: 1,
            condition: { context in
                return context.route.difficulty == "hard" ||
                       context.route.length > 3.0
            }
        )
    ]
    
    private func weatherData(from response: WeatherResponse) -> WeatherData {
        let main = (response.current.weather.first?.main ?? "").lowercased()

        // Rules currently check for substrings: "sun", "rain", "cloud", "storm"
        let mappedCondition: String
        if main.contains("clear") {
            mappedCondition = "sunny"
        } else if main.contains("thunder") {
            mappedCondition = "storm"
        } else if main.contains("rain") || main.contains("drizzle") {
            mappedCondition = "rain"
        } else if main.contains("cloud") {
            mappedCondition = "cloudy"
        } else if main.contains("mist") || main.contains("fog") || main.contains("haze") {
            mappedCondition = "partly cloudy"
        } else {
            // Fall back to something that will still match rule substrings.
            mappedCondition = main.contains("cloud") ? "cloudy" : (main.isEmpty ? "partly cloudy" : main)
        }

        let precipitationChance: Double
        if let oneHourRain = response.current.rain?.oneHour {
            // Rough heuristic: 0..5mm in the next hour => 0..1 probability.
            precipitationChance = min(1.0, max(0.0, oneHourRain / 5.0))
        } else if mappedCondition == "rain" || mappedCondition == "storm" {
            precipitationChance = 0.6
        } else {
            precipitationChance = 0.0
        }

        let uvIndex = Int(round(response.current.uvi))

        let tempBand: String
        if response.current.temp >= 80 {
            tempBand = "hot"
        } else if response.current.temp <= 55 {
            tempBand = "cold"
        } else {
            tempBand = mappedCondition
        }

        return WeatherData(
            condition: mappedCondition,
            main: tempBand,
            temperature: response.current.temp,
            uvIndex: uvIndex,
            precipitationChance: precipitationChance,
            windSpeed: response.current.wind_speed,
            humidity: response.current.humidity
        )
    }

    /// Builds suggestions using *current* weather from `weatherViewModel.weather` (OpenWeather "current").
    /// If weather isn't loaded yet, it triggers a fetch via the view model.
    func suggestions(
        for route: Route,
        at timeOfDay: Date = Date(),
        location: CLLocationCoordinate2D,
        weatherViewModel: WeatherViewModel,
        timeoutSeconds: TimeInterval = 10
    ) async -> [Suggestion] {
        if weatherViewModel.weather == nil {
            weatherViewModel.fetchWeather(lat: location.latitude, lon: location.longitude)

            let start = Date()
            while weatherViewModel.weather == nil,
                  Date().timeIntervalSince(start) < timeoutSeconds {
                try? await Task.sleep(nanoseconds: 250_000_000) // 0.25s
            }
        }

        guard let weatherResponse = weatherViewModel.weather else { return [] }
        let weather = weatherData(from: weatherResponse)
        let context = Context(route: route, timeOfDay: timeOfDay, weather: weather)

        return rules
            .filter { $0.condition(context) }
            .sorted { $0.priority < $1.priority }
    }
}

// Add to Context extension
extension Context {
    func isMidday() -> Bool {
        let hour = Calendar.current.component(.hour, from: timeOfDay)
        return hour >= 11 && hour <= 14
    }

    func isDusk() -> Bool {
        let hour = Calendar.current.component(.hour, from: timeOfDay)
        return hour >= 18 && hour <= 21
    }

    func isEarlyMorning() -> Bool {
        let hour = Calendar.current.component(.hour, from: timeOfDay)
        return hour >= 5 && hour <= 7
    }
}

// Update WeatherData model
struct WeatherData {
    let condition: String  // "sunny", "rain", "cloudy", "partly cloudy"
    let main: String       // "hot", "cold", or a weather-derived string
    let temperature: Double
    let uvIndex: Int?
    let precipitationChance: Double  // 0.0 to 1.0
    let windSpeed: Double  // mph
    let humidity: Int  // 0 to 100
}
