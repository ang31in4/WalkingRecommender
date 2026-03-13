import Foundation
import CoreLocation
import MapKit
import Combine

extension CLLocationCoordinate2D {
    static let uci = CLLocationCoordinate2D(latitude: 33.6405, longitude: -117.8443)
}

class LocationSearch: NSObject, ObservableObject, CLLocationManagerDelegate, MKLocalSearchCompleterDelegate {
    @Published var searchText: String = ""
    @Published var searchCompletions: [MKLocalSearchCompletion] = []
    @Published var searchedCoordinate: CLLocationCoordinate2D?
    @Published var currentCoordinate: CLLocationCoordinate2D?
    @Published var isSearching: Bool = false
    var isSearch: Bool = false

    var activeLocation: CLLocationCoordinate2D {
        if let searched = searchedCoordinate {
            return searched
        }
        if let current = currentCoordinate {
            return current
        }
        return .uci
    }

    /// Stable id for observing location changes
    var activeLocationId: String {
        "\(activeLocation.latitude),\(activeLocation.longitude)"
    }

    /// Display name for weather card and other UI
    var locationDisplayName: String {
        if searchedCoordinate != nil, !searchText.isEmpty {
            return searchText
        }
        if currentCoordinate != nil {
            return "Current location"
        }
        return "UCI"
    }

    private let locationManager = CLLocationManager()
    private let searchCompleter = MKLocalSearchCompleter()
    private var searchCancellable: AnyCancellable?

    override init() {
        super.init()
        locationManager.delegate = self
        locationManager.requestWhenInUseAuthorization()
        locationManager.startUpdatingLocation()

        searchCompleter.delegate = self
        searchCompleter.resultTypes = [.address, .pointOfInterest]
        searchCompleter.region = MKCoordinateRegion(
            center: CLLocationCoordinate2D.uci,
            span: MKCoordinateSpan(latitudeDelta: 2.0, longitudeDelta: 2.0)
        )

        searchCancellable = $searchText
            .debounce(for: .milliseconds(300), scheduler: RunLoop.main)
            .removeDuplicates()
            .sink { [weak self] query in
                self?.searchCompleter.queryFragment = query
            }
    }

    func locationManager(_ location: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.first else { return }
        if currentCoordinate == nil {
            self.currentCoordinate = location.coordinate
            searchCompleter.region = MKCoordinateRegion(
                center: location.coordinate,
                span: MKCoordinateSpan(latitudeDelta: 0.5, longitudeDelta: 0.5)
            )
        }
        locationManager.stopUpdatingLocation()
    }

    func completerDidUpdateResults(_ completer: MKLocalSearchCompleter) {
        searchCompletions = completer.results
    }

    func completer(_ completer: MKLocalSearchCompleter, didFailWithError error: Error) {
        searchCompletions = []
    }

    func getGEOJSON() -> [Double]? {
        let coordinatesData = activeLocation
        return [coordinatesData.longitude, coordinatesData.latitude]
    }

    /// Params for route API: latitude, longitude, minDistanceM, maxDistanceM
    func routeParams() -> (latitude: Double, longitude: Double) {
        (activeLocation.latitude, activeLocation.longitude)
    }

    func selectCompletion(_ completion: MKLocalSearchCompletion) {
        let request = MKLocalSearch.Request(completion: completion)
        let search = MKLocalSearch(request: request)
        isSearching = true
        searchCompletions = []

        search.start { [weak self] response, error in
            DispatchQueue.main.async {
                self?.isSearching = false
                if let error = error {
                    print("Search error: \(error.localizedDescription)")
                    return
                }
                if let item = response?.mapItems.first {
                    self?.searchedCoordinate = item.placemark.coordinate
                    self?.searchText = item.name ?? completion.title
                }
            }
        }
    }

    func performSearch() {
        guard !searchText.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        let request = MKLocalSearch.Request()
        request.naturalLanguageQuery = searchText
        let search = MKLocalSearch(request: request)
        isSearching = true
        searchCompletions = []

        search.start { [weak self] response, error in
            DispatchQueue.main.async {
                self?.isSearching = false
                if let error = error {
                    print("Error: \(error.localizedDescription)")
                    return
                }
                if let item = response?.mapItems.first {
                    self?.searchedCoordinate = item.placemark.coordinate
                    self?.searchText = item.name ?? item.placemark.title ?? self?.searchText ?? ""
                }
            }
        }
    }
}
