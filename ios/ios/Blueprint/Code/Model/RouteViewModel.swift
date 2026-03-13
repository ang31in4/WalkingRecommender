import Combine

class RouteViewModel: ObservableObject {
    @Published var allRoutes: [Route] = []
    @Published var displayedRoutes: [Route] = []

    var currentFilter: FilterModel = FilterModel()

    private func matchesFilter(_ route: Route, _ filter: FilterModel) -> Bool {
        
        if let difficulty = filter.selectedDifficulty {
            let routeDiff = route.difficulty.lowercased()
            let filterRaw = difficulty.rawValue.lowercased()
            // Backend may use "difficult" instead of "hard"
            let matches = routeDiff == filterRaw || (routeDiff == "difficult" && filterRaw == "hard") || (routeDiff == "hard" && filterRaw == "difficult")
            if !matches { return false }
        }

      
        if let distance = filter.selectedDistance {
            let miles = route.length
            let matchesDistance: Bool
            switch distance {
            case .lessThanHalfMile: matchesDistance = miles < 0.5
            case .fromHalfTo1Mile: matchesDistance = miles >= 0.5 && miles <= 1.0
            case .greaterThan1Mile: matchesDistance = miles > 1.0
            }
            if !matchesDistance { return false }
        }


        if !filter.selectedSuitability.isEmpty {
            for suitability in filter.selectedSuitability {
                let routeValue: Bool?
                switch suitability {
                case .petFriendly: routeValue = route.petFriendly
                case .wheelchairAccessible: routeValue = route.wheelchairAccessible
                case .urban: routeValue = route.urban
                }
                if routeValue != true { return false }
            }
        }

        return true
    }

    @discardableResult
    func applyFilter(_ filter: FilterModel) -> [Route] {
        currentFilter = filter
        displayedRoutes = allRoutes.filter { matchesFilter($0, filter) }
        return displayedRoutes
    }
}
