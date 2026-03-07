import Foundation
import Combine
import CoreLocation

private let WEATHER_API_BASE = "https://api.openweathermap.org/data/3.0/onecall"
private let WEATHER_API_KEY = "284009ac85bf1af360cd32ac0fbf9d40"

func weatherURL(lat: Double, lon: Double) -> String {
    "\(WEATHER_API_BASE)?lat=\(lat)&lon=\(lon)&units=imperial&appid=\(WEATHER_API_KEY)"
}

func getWeatherInNHours(hourly: [Hourly], number_of_hours: Int) -> [Hourly] {
    var hour_in_range: [Hourly] = []
    for i in 0..<number_of_hours {
        hour_in_range.append(hourly[i])
    }
    return hour_in_range;
}

class WeatherService {
    func getWeather(lat: Double, lon: Double) -> AnyPublisher<WeatherResponse, Error> {
        let urlString = weatherURL(lat: lat, lon: lon)
        guard let url = URL(string: urlString) else {
            return Fail(error: URLError(.badURL)).eraseToAnyPublisher()
        }
        return URLSession.shared.dataTaskPublisher(for: url)
            .map(\.data)
            .decode(type: WeatherResponse.self, decoder: JSONDecoder())
            .eraseToAnyPublisher()
    }
}

class WeatherViewModel: ObservableObject {
    private let weatherService = WeatherService()
    private var cancellable: AnyCancellable?
    private var refreshTimer: Timer?
    @Published var weather: WeatherResponse?

    func fetchWeather(lat: Double, lon: Double) {
        cancellable?.cancel()
        cancellable = weatherService.getWeather(lat: lat, lon: lon)
            .receive(on: DispatchQueue.main)
            .sink(receiveCompletion: { _ in }, receiveValue: { [weak self] weather in
                self?.weather = weather
            })
    }

    func startHourlyRefresh(lat: Double, lon: Double) {
        refreshTimer?.invalidate()
        fetchWeather(lat: lat, lon: lon)
        refreshTimer = Timer.scheduledTimer(withTimeInterval: 3600, repeats: true) { [weak self] _ in
            self?.fetchWeather(lat: lat, lon: lon)
        }
        RunLoop.main.add(refreshTimer!, forMode: .common)
    }

    func updateLocation(lat: Double, lon: Double) {
        startHourlyRefresh(lat: lat, lon: lon)
    }

    func stopRefresh() {
        refreshTimer?.invalidate()
        refreshTimer = nil
    }
}
