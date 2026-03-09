import Foundation
import SwiftUI
internal import _LocationEssentials

struct RouteCard: View {
    let route: Route

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(route.name)
                .font(.headline)
                .foregroundColor(.primary)
            Text(String(format: "%.2f mi", route.length))
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .frame(height: 100)
        .background(Color.blue.opacity(0.3))
        .cornerRadius(10)
        .shadow(color: Color.black.opacity(0.1), radius: 5)
    }
}

struct RouteCard_AllCategories: View {
    @ObservedObject var filterViewModel: FilterViewModel
    @ObservedObject var locationSearch: LocationSearch
    var userId: String?
    var onRouteSelected: ((Route) -> Void)?
    @State private var originalRoutes: [Route] = []
    @State private var allRoutes: [Route] = []
    @State private var isLoading = true
    @State private var isLoadingSupplement = false

    private var filteredRoutes: [Route] {
        filterRoutes(allRoutes, by: filterViewModel.currentFilter)
    }

    private var filterChangeId: String {
        let f = filterViewModel.currentFilter
        return "\(f.selectedDistance?.rawValue ?? "nil")-\(f.selectedDifficulty?.rawValue ?? "nil")-\(f.selectedSuitability.count)"
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            if isLoading {
                ProgressView("Loading routes…")
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding()
            } else if isLoadingSupplement {
                ProgressView("Fetching more routes…")
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding()
            } else if filteredRoutes.isEmpty {
                Text(allRoutes.isEmpty ? "No routes available for this location. Try UCI area or adjust filters." : "No routes match your filters")
                    .foregroundColor(.secondary)
            } else {
                Text("Suggested for you")
                    .font(.title2)
                    .fontWeight(.semibold)
                ScrollView(.vertical, showsIndicators: true) {
                    LazyVGrid(columns: [GridItem(.flexible(), spacing: 12), GridItem(.flexible(), spacing: 12)], spacing: 12) {
                        ForEach(filteredRoutes.prefix(10)) { route in
                            RouteCard(route: route)
                                .onTapGesture { onRouteSelected?(route) }
                        }
                    }
                }
            }
        }
        .task(id: "\(locationSearch.activeLocation.latitude)-\(locationSearch.activeLocation.longitude)") {
            let (minM, maxM) = (100.0, 5000.0)
            let (lat, lon, minDM, maxDM) = locationSearch.routeParams(minDistanceM: minM, maxDistanceM: maxM)
            let fromAPI = await loadGeoJsonFromAPI(
                latitude: lat,
                longitude: lon,
                minDistanceM: minDM,
                maxDistanceM: maxDM,
                userId: userId
            )
            let routes = fromAPI
            originalRoutes = routes
            allRoutes = routes
            isLoading = false
        }
        .onChange(of: filterChangeId) { _, _ in checkAndFetchSupplement() }
    }

    private func checkAndFetchSupplement() {
        guard !filterViewModel.currentFilter.isDefault else {
            allRoutes = originalRoutes
            return
        }
        let filtered = filterRoutes(allRoutes, by: filterViewModel.currentFilter)
        guard filtered.count < 10 else { return }

        Task {
            await fetchWithFilterParams()
        }
    }

    private func fetchWithFilterParams() async {
        isLoadingSupplement = true
        let (minM, maxM) = DistanceRange.minMaxMeters(for: filterViewModel.currentFilter.selectedDistance)
        let (lat, lon, minDM, maxDM) = locationSearch.routeParams(minDistanceM: minM, maxDistanceM: maxM)
        let fromAPI = await loadGeoJsonFromAPI(
            latitude: lat,
            longitude: lon,
            minDistanceM: minDM,
            maxDistanceM: maxDM,
            userId: userId
        )
        allRoutes = fromAPI
        isLoadingSupplement = false
    }
}

