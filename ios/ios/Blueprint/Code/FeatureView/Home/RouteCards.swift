import Foundation
import SwiftUI
internal import _LocationEssentials

private struct RoutesScrollOffsetKey: PreferenceKey {
    static var defaultValue: CGFloat = 0
    static func reduce(value: inout CGFloat, nextValue: () -> CGFloat) { value = nextValue() }
}

struct RouteCard: View {
    let route: Route

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(route.name)
                .font(.headline)
                .foregroundColor(.primary)
            Text(String(format: "%.0f mi", route.length))
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
//    @State private var originalRoutes: [Route] = []
    @State private var routes: [Route] = []
    @State private var isLoading = true
    @State private var isLoadingSupplement = false
    @State private var lastScrollOffset: CGFloat = .nan

    private var filteredRoutes: [Route] {
        filterRoutes(routes, by: filterViewModel.currentFilter)
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
                Text(routes.isEmpty ? "No routes available for this location. Try UCI area or adjust filters." : "No routes match your filters")
                    .foregroundColor(.secondary)
            } else {
                ScrollViewReader { proxy in
                    HStack(alignment: .firstTextBaseline) {
                        Text("Suggested for you")
                            .font(.title2)
                            .fontWeight(.semibold)
                        Spacer()
                        Button("Scroll to bottom") {
                            print("[RouteCards] scrollToBottom tapped")
                            guard let last = filteredRoutes.last else { return }
                            withAnimation(.easeOut(duration: 0.25)) {
                                proxy.scrollTo(last.id, anchor: .bottom)
                            }
                        }
                        .font(.caption)
                    }

                    ScrollView(.vertical, showsIndicators: true) {
                        LazyVStack(spacing: 12) {
                            GeometryReader { g in
                                Color.clear.preference(
                                    key: RoutesScrollOffsetKey.self,
                                    value: g.frame(in: .named("routesScroll")).minY
                                )
                            }
                            .frame(height: 0)

                            ForEach(filteredRoutes) { route in
                                RouteCard(route: route)
                                    .id(route.id)
                                    .frame(maxWidth: .infinity)
                                    .contentShape(Rectangle())
                                    .onTapGesture { onRouteSelected?(route) }
                            }
                        }
                        .padding(.vertical, 4)
                    }
                    .coordinateSpace(name: "routesScroll")
                    .layoutPriority(1)
                    .frame(minHeight: 0, maxHeight: .infinity)
                    .onAppear { print("[RouteCards] Showing \(filteredRoutes.count) routes in scroll view") }
                    .onPreferenceChange(RoutesScrollOffsetKey.self) { offset in
                        if lastScrollOffset.isNaN {
                            lastScrollOffset = offset
                            print("[RouteCards] initial scroll offset \(offset)")
                            return
                        }
                        if abs(offset - lastScrollOffset) >= 2 {
                            print("[RouteCards] scroll offset \(offset)")
                            lastScrollOffset = offset
                        }
                    }
                }
            }
        }
        .frame(minHeight: 0, maxHeight: .infinity)
        .task(id: "\(locationSearch.activeLocation.latitude)-\(locationSearch.activeLocation.longitude)") {
            let (minM, maxM) = (100.0, 16093.0)
            let (lat, lon, minDM, maxDM) = locationSearch.routeParams(minDistanceM: minM, maxDistanceM: maxM)
            let fromAPI = await loadGeoJsonFromAPI(
                latitude: lat,
                longitude: lon,
                minDistanceM: minDM,
                maxDistanceM: maxDM,
                userId: userId
            )
            routes = fromAPI
            isLoading = false
            print("[RouteCards] Routes loaded: \(routes.count) from API")
            
//            originalRoutes = routes
//            allRoutes = routes
//            // If filters are on and we have fewer than 10 after filtering, fetch more matching routes
//            if !filterViewModel.currentFilter.isDefault,
//               filterRoutes(routes, by: filterViewModel.currentFilter).count < 10 {
//                await fetchWithFilterParams()
//            }
        }
//        .onChange(of: filterChangeId) { _, _ in checkAndFetchSupplement() }
    }

//    private func checkAndFetchSupplement() {
//        guard !filterViewModel.currentFilter.isDefault else {
//            allRoutes = originalRoutes
//            return
//        }
//        let filtered = filterRoutes(allRoutes, by: filterViewModel.currentFilter)
//        guard filtered.count < 30 else { return }
//
//        Task {
//            await fetchWithFilterParams()
//        }
//    }
//
//    private func fetchWithFilterParams() async {
//        isLoadingSupplement = true
//        let (minM, maxM) = DistanceRange.minMaxMeters(for: filterViewModel.currentFilter.selectedDistance)
//        let (lat, lon, minDM, maxDM) = locationSearch.routeParams(minDistanceM: minM, maxDistanceM: maxM)
//        let fromAPI = await loadGeoJsonFromAPI(
//            latitude: lat,
//            longitude: lon,
//            minDistanceM: minDM,
//            maxDistanceM: maxDM,
//            userId: userId
//        )
//        routes = fromAPI
//        isLoadingSupplement = false
//    }
}

