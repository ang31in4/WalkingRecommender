import Foundation

/// Base URL for backend API. Change to your Mac's IP (e.g. "http://192.168.1.100:5050")
/// when running the app on a physical device; localhost only works in Simulator.
enum APIConfig {
    static let baseURL = "http://localhost:5050"
}
