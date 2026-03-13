import Combine

class RouteViewModel {
    var allRoutes: [Route] = []
    var displayedRoutes: [Route] = []
    
    var currentFilter: FilterModel = FilterModel()

    /// Returns true if the route matches the filter. Empty filter categories are ignored.
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
            // Route model has no suitability property yet; when added, require route to match at least one selected suitability.
            // For now we do not filter by suitability so routes are still shown.
        }

        return true
    }

    /// Returns routes that match the filter. Empty filter categories are not applied.
    func applyFilter(_ filter: FilterModel) -> [Route] {
        currentFilter = filter
        displayedRoutes = allRoutes.filter { matchesFilter($0, filter) }
        return displayedRoutes
    }
}
