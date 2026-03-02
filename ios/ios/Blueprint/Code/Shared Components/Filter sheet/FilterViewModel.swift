import Foundation
import SwiftUI
import Combine

class FilterViewModel: ObservableObject {
    @Published var currentFilter: FilterModel = FilterModel()
    @Published var isFilterSheetPresented: Bool = false

    var activeFiltersCount: Int {
        var count = 0
        if currentFilter.selectedDifficulty != nil { count += 1 }
        if currentFilter.selectedDistance != nil { count += 1 }
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
        objectWillChange.send()
        if selected {
            currentFilter.selectedSuitability.insert(suitability)
        } else {
            currentFilter.selectedSuitability.remove(suitability)
        }
    }

    func setDifficulty(_ difficulty: RouteDifficulty) {
        objectWillChange.send()
        currentFilter.selectedDifficulty = currentFilter.selectedDifficulty == difficulty ? nil : difficulty
    }

    func setDistance(_ distance: DistanceRange) {
        objectWillChange.send()
        currentFilter.selectedDistance = currentFilter.selectedDistance == distance ? nil : distance
    }
}
