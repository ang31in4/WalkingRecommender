import SwiftUI
import CoreLocation

struct WeatherSuggestionPanel: View {
    let location: CLLocationCoordinate2D
    let locationName: String
    let filter: FilterModel

    @StateObject private var weatherViewModel = WeatherViewModel()
    @State private var suggestions: [Suggestion] = []
    @State private var weatherPills: [String] = []
    @State private var loadTask: Task<Void, Never>?

    var body: some View {
        VStack(spacing: 16) {
            Text("Current weather at \(locationName)")
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(.black)

            HStack(spacing: 8) {
                ForEach(weatherPills.prefix(3), id: \.self) { pill in
                    Text(pill)
                        .font(.caption)
                        .fontWeight(.semibold)
                        .padding(.horizontal, 14)
                        .padding(.vertical, 8)
                        .background(Color.green)
                        .foregroundColor(.white)
                        .clipShape(Capsule())
                }
            }

            VStack(alignment: .leading, spacing: 10) {
                Text("Suggested before you enjoy the routes")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.black)

                if suggestions.isEmpty {
                    Text("Loading suggestions…")
                        .font(.system(size: 13))
                        .foregroundColor(.secondary)
                } else {
                    ForEach(suggestions, id: \.id) { suggestion in
                        HStack(alignment: .top, spacing: 8) {
                            Image(systemName: "checkmark.circle.fill")
                                .font(.system(size: 14))
                                .foregroundColor(.green)
                            Text(suggestion.message)
                                .font(.system(size: 13))
                                .foregroundColor(.black)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                }
            }
            .padding(18)
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: 14))

            RollingTriangle()
                .frame(width: 54, height: 54)

            Text("Loading the routes…")
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(.black)
        }
        .padding(22)
        .frame(maxWidth: .infinity)
        .background(
            RoundedRectangle(cornerRadius: 22)
                .fill(Color.white)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 22)
                .stroke(Color.black.opacity(0.08), lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(0.12), radius: 10, x: 0, y: 6)
        .shadow(color: Color.black.opacity(0.06), radius: 2, x: 0, y: 1)
        .padding(.horizontal, 18)
        .onAppear {
            loadTask?.cancel()
            loadTask = Task {
                await loadSuggestions()
            }
        }
        .onDisappear {
            loadTask?.cancel()
            loadTask = nil
        }
    }

    private func routeLengthEstimate() -> Double {
        switch filter.selectedDistance {
        case .lessThanHalfMile:
            return 0.3
        case .fromHalfTo1Mile:
            return 0.75
        case .greaterThan1Mile:
            return 2.5
        case .none:
            return 2.2
        }
    }

    private func difficultyEstimate() -> String {
        filter.selectedDifficulty?.rawValue ?? "moderate"
    }

    private func placeholderRoute() -> Route {
        let len = routeLengthEstimate()
        let coords: [CLLocationCoordinate2D] = [
            location,
            CLLocationCoordinate2D(latitude: location.latitude + 0.002, longitude: location.longitude + 0.002),
        ]

        let pet = filter.selectedSuitability.contains(.petFriendly)
        let wheel = filter.selectedSuitability.contains(.wheelchairAccessible)
        let urban = filter.selectedSuitability.contains(.urban)

        return Route(
            name: "Suggested Route",
            difficulty: difficultyEstimate(),
            coordinates: coords,
            length: len,
            petFriendly: pet,
            wheelchairAccessible: wheel,
            urban: urban
        )
    }

    private func mapConditionTag(from response: WeatherResponse) -> String {
        // Hot/Cold takes priority over weather icon mapping.
        // Keep thresholds aligned with SuggestionEngine's WeatherData.main.
        if response.current.temp >= 80 {
            return "Hot"
        }
        if response.current.temp <= 55 {
            return "Cold"
        }

        let main = (response.current.weather.first?.main ?? "").lowercased()
        if main.contains("clear") {
            return "Sunny"
        }
        if main.contains("thunder") {
            return "Storm"
        }
        if main.contains("rain") || main.contains("drizzle") {
            return "Rain"
        }
        if main.contains("cloud") {
            return "Cloudy"
        }
        if main.isEmpty {
            return "Weather"
        }
        return main.capitalized
    }

    private func mapWeatherPills(from response: WeatherResponse) -> [String] {
        // Show 2-3 "right now" weather conditions as green pills.
        // Includes Hot/Cold as a primary tag.
        var pills: [String] = []

        if response.current.temp >= 80 {
            pills.append("Hot")
        } else if response.current.temp <= 55 {
            pills.append("Cold")
        } else {
            pills.append("Mild")
        }

        let mains = response.current.weather.map { $0.main.lowercased() }
        for main in mains {
            let mapped: String
            if main.contains("clear") {
                mapped = "Sunny"
            } else if main.contains("thunder") {
                mapped = "Storm"
            } else if main.contains("rain") || main.contains("drizzle") {
                mapped = "Rain"
            } else if main.contains("cloud") {
                mapped = "Cloudy"
            } else {
                mapped = main.capitalized
            }

            if !pills.contains(mapped) {
                pills.append(mapped)
            }

            if pills.count >= 3 {
                break
            }
        }

        if pills.isEmpty {
            pills = ["Weather"]
        }

        return pills
    }

    private func loadSuggestions() async {
        // Trigger weather fetch; SuggestionEngine also fetches if needed, but we want the tag ASAP.
        weatherViewModel.fetchWeather(lat: location.latitude, lon: location.longitude)

        let start = Date()
        while weatherViewModel.weather == nil,
              Date().timeIntervalSince(start) < 10 {
            try? await Task.sleep(nanoseconds: 250_000_000)
        }

        if let weather = weatherViewModel.weather {
            weatherPills = mapWeatherPills(from: weather)
        }

        let engine = SuggestionEngine()
        let computed = await engine.suggestions(
            for: placeholderRoute(),
            at: Date(),
            location: location,
            weatherViewModel: weatherViewModel
        )

        await MainActor.run {
            self.suggestions = computed
        }
    }
}

private struct RollingTriangle: View {
    var body: some View {
        TimelineView(.animation) { timeline in
            // Deterministic continuous rotation using time.
            // 180 degrees/sec => one full rotation every 2 seconds.
            let angle = timeline.date.timeIntervalSinceReferenceDate * 180.0
            TriangleShape()
                .fill(Color.green)
                .rotationEffect(.degrees(angle))
        }
    }
}

private struct TriangleShape: Shape {
    func path(in rect: CGRect) -> Path {
        let w = rect.width
        let h = rect.height
        var path = Path()
        path.move(to: CGPoint(x: w / 2, y: 0))
        path.addLine(to: CGPoint(x: w, y: h))
        path.addLine(to: CGPoint(x: 0, y: h))
        path.closeSubpath()
        return path
    }
}

#Preview("Weather suggestion panel") {
    WeatherSuggestionPanel(
        location: CLLocationCoordinate2D(latitude: 33.6405, longitude: -117.8443),
        locationName: "Sample location",
        filter: FilterModel()
    )
}

