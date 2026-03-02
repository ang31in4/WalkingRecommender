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
        .frame(width: UIScreen.main.bounds.width * 2/5, alignment: .leading)
        .padding()
        .frame(height: 100)
        .background(Color.blue.opacity(0.3))
        .cornerRadius(10)
        .shadow(color: Color.black.opacity(0.1), radius: 5)
    }
}

struct RouteCard_SameCategory: View {
    let title: String
    let routes: [Route]

    var body: some View {
        VStack(alignment: .leading) {
            Text(title)
                .font(.title2)
                .fontWeight(.semibold)
            ScrollView(.horizontal) {
                HStack {
                    ForEach(routes.prefix(3)) { route in
                        RouteCard(route: route)
                    }
                }
            }
        }
    }
}

struct RouteCard_AllCategories: View {
    @ObservedObject var filterViewModel: FilterViewModel
    @ObservedObject var locationSearch: LocationSearch
    @State private var allRoutes: [Route] = []
    @State private var isLoading = true

    private var filteredRoutes: [Route] {
        filterRoutes(allRoutes, by: filterViewModel.currentFilter)
    }

    private let categoryTitles = ["Suggested for you", "Top paths nearby", "A traffic-free zone"]

    var body: some View {
        VStack(alignment: .leading, spacing: 24) {
            if isLoading {
                ProgressView("Loading routes…")
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding()
            } else if filteredRoutes.isEmpty {
                Text("No routes match your filters")
                    .foregroundColor(.secondary)
            } else {
                ForEach(Array(categoryTitles.enumerated()), id: \.offset) { index, title in
                    let start = index * 3
                    let categoryRoutes = Array(filteredRoutes.dropFirst(start).prefix(3))
                    if !categoryRoutes.isEmpty {
                        RouteCard_SameCategory(title: title, routes: categoryRoutes)
                    }
                }
            }
        }
        .task(id: "\(locationSearch.activeLocation.latitude)-\(locationSearch.activeLocation.longitude)-\(filterViewModel.currentFilter.selectedDistance?.rawValue ?? "nil")-\(filterViewModel.currentFilter.selectedDifficulty?.rawValue ?? "nil")") {
            let (minM, maxM) = DistanceRange.minMaxMeters(for: filterViewModel.currentFilter.selectedDistance)
            let (lat, lon, minDM, maxDM) = locationSearch.routeParams(minDistanceM: minM, maxDistanceM: maxM)
            let fromAPI = await loadGeoJsonFromAPI(
                latitude: lat,
                longitude: lon,
                minDistanceM: minDM,
                maxDistanceM: maxDM
            )
            allRoutes = fromAPI.isEmpty ? loadGeoJson() : fromAPI
            isLoading = false
        }
    }
}

