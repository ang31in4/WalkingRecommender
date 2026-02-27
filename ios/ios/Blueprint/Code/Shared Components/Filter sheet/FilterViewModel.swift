import Foundation
import SwiftUI
import Combine

class FilterViewModel: ObservableObject {
    @Published var currentFilter: FilterModel = FilterModel()
    @Published var isFilterSheetPresented: Bool = false

    var activeFiltersCount: Int {
        var count = 2
        count += currentFilter.selectedSuitability.count
        return count
    }

    func showFilterSheet() {
        isFilterSheetPresented = true
    }

    func dismissFilterSheet() {
        isFilterSheetPresented = false
    }

    func applyFilter() {
        dismissFilterSheet()
    }

    func clearFilters() {
        currentFilter.clear()
    }

    func setSuitability(_ suitability: Suitability, selected: Bool) {
        if selected {
            currentFilter.selectedSuitability.insert(suitability)
        } else {
            currentFilter.selectedSuitability.remove(suitability)
        }
    }

    func setDifficulty(_ difficulty: RouteDifficulty) {
        currentFilter.selectedDifficulty = difficulty
    }

    func setDistance(_ distance: DistanceRange) {
        currentFilter.selectedDistance = distance
    }
}
