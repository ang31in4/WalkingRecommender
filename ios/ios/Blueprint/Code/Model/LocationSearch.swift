import Foundation
import CoreLocation
import MapKit
import Combine

extension CLLocationCoordinate2D {
    static let uci = CLLocationCoordinate2D(latitude: 33.6405, longitude: -117.8443)
}

class LocationSearch: NSObject, ObservableObject, CLLocationManagerDelegate {
    @Published var searchText: String = ""
    @Published var searchedCoordinate: CLLocationCoordinate2D?
    @Published var currentCoordinate: CLLocationCoordinate2D?
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
    private let locationManager = CLLocationManager()
    
    override init() {
        super.init()
        locationManager.delegate = self
        locationManager.requestWhenInUseAuthorization()
        locationManager.startUpdatingLocation()
    }
    
    func locationManager(_ location:CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.first else { return }
        if currentCoordinate == nil {
            self.currentCoordinate = location.coordinate
        }
        locationManager.stopUpdatingLocation()
    }
    
    func getGEOJSON() -> [Double]? {
        let coordinatesData = activeLocation
        return [coordinatesData.longitude, coordinatesData.latitude]
    }
    
    func performSearch() {
        isSearch = true
        let request = MKLocalSearch.Request()
        let search = MKLocalSearch(request: request)
        search.start {response, error in
            DispatchQueue.main.async { [self] in
                isSearch = false
                if let error = error {
                    print("Error: \(error.localizedDescription)")
                    return
                }
                if let firstMatch = response?.mapItems.first {
                    searchedCoordinate = firstMatch.location.coordinate
                    print("Found coordinates: \(String(describing: searchedCoordinate))")
                }
            }
        }
    }
}
