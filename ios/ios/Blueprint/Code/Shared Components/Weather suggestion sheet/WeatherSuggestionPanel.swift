import SwiftUI
import CoreLocation

struct WeatherSuggestionPanel: View {
    let location: CLLocationCoordinate2D
    let filter: FilterModel

    @StateObject private var weatherViewModel = WeatherViewModel()
    @State private var conditionTag: String? = nil
    @State private var suggestions: [Suggestion] = []
    @State private var loadTask: Task<Void, Never>?

    var body: some View {
        VStack(spacing: 14) {
            HStack {
                Spacer()
                if let tag = conditionTag {
                    Text(tag)
                        .font(.caption)
                        .fontWeight(.semibold)
                        .padding(.horizontal, 14)
                        .padding(.vertical, 8)
                        .background(Color.yellow)
                        .foregroundColor(.white)
                        .clipShape(Capsule())
                } else {
                    ProgressView()
                        .progressViewStyle(.circular)
                        .tint(.white)
                }
                Spacer()
            }

            VStack(alignment: .leading, spacing: 10) {
                Text("Suggested before you enjoy the routes")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.white)

                if suggestions.isEmpty {
                    Text("Loading suggestions…")
                        .font(.system(size: 13))
                        .foregroundColor(.white)
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
            .padding(16)
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: 14))

            RollingTriangle()
                .frame(width: 46, height: 46)

            Text("Loading the routes…")
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(.white)
        }
        .padding(18)
        .frame(maxWidth: .infinity)
        .background(
            RoundedRectangle(cornerRadius: 22)
                .fill(Color.green)
        )
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

    private func loadSuggestions() async {
        // Trigger weather fetch; SuggestionEngine also fetches if needed, but we want the tag ASAP.
        weatherViewModel.fetchWeather(lat: location.latitude, lon: location.longitude)

        let start = Date()
        while weatherViewModel.weather == nil,
              Date().timeIntervalSince(start) < 10 {
            try? await Task.sleep(nanoseconds: 250_000_000)
        }

        if let weather = weatherViewModel.weather {
            conditionTag = mapConditionTag(from: weather)
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
                .fill(Color.white)
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
        filter: FilterModel()
    )
}

