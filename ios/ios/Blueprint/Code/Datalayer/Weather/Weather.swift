import Foundation
import Combine

//let WEATHER_API = "https://api.openweathermap.org/data/2.5/weather?q=Irvine,CA,US&appid=284009ac85bf1af360cd32ac0fbf9d40&units=metric"
private let WEATHER_API = "https://api.openweathermap.org/data/3.0/onecall?lat=33.6846&lon=-11.8265&units=metric&appid=284009ac85bf1af360cd32ac0fbf9d40"

func getWeatherInNHours(hourly: [Hourly], number_of_hours: Int) -> [Hourly] {
    var hour_in_range: [Hourly] = []
    for i in 0..<number_of_hours {
        hour_in_range.append(hourly[i])
    }
    return hour_in_range;
}

class WeatherService {
    let api_url = URL(string: WEATHER_API)!
    func getWeather(url: String) -> AnyPublisher<WeatherResponse, Error> {
        return URLSession.shared.dataTaskPublisher(for: api_url)
            .map(\.data)
            .decode(type: WeatherResponse.self, decoder: JSONDecoder())
            .eraseToAnyPublisher()
    }
}

class WeatherViewModel: ObservableObject {
    private let weather_service = WeatherService()
    private var cancellable: AnyCancellable?
    @Published var weather: WeatherResponse?
    
    func fetchWeather() {
        cancellable = weather_service.getWeather(url: WEATHER_API)
            .receive(on: DispatchQueue.main)
            .sink(receiveCompletion: { _ in }, receiveValue: { weather in self.weather = weather })
    }
}
