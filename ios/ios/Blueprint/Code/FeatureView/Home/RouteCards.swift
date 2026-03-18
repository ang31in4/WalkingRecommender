import Foundation
import SwiftUI
import CoreLocation
internal import _LocationEssentials

private struct RoutesScrollOffsetKey: PreferenceKey {
    static var defaultValue: CGFloat = 0
    static func reduce(value: inout CGFloat, nextValue: () -> CGFloat) { value = nextValue() }
}

struct RouteCard: View {
    let route: Route
    let userLocation: CLLocation

    @State private var unsplashImageURL: String?

    private func photoCategory(for route: Route) -> PhotoCategory {
        route.urban == true ? .urban : .trail
    }

    var body: some View {
        let distanceMiles: Double? = {
            guard let meters = route.distanceFromStart(from: userLocation) else { return nil }
            return meters / 1609.34
        }()

        VStack(alignment: .leading, spacing: 0) {
            // Unsplash image at top
            ZStack {
                Color.gray.opacity(0.2)
                if let urlString = unsplashImageURL, let url = URL(string: urlString) {
                    AsyncImage(url: url) { phase in
                        switch phase {
                        case .success(let image):
                            image
                                .resizable()
                                .aspectRatio(contentMode: .fill)
                        case .failure:
                            Image(systemName: "photo.on.rectangle.angled")
                                .font(.title)
                                .foregroundColor(.gray)
                        case .empty:
                            ProgressView()
                        @unknown default:
                            EmptyView()
                        }
                    }
                } else {
                    Image(systemName: "photo.on.rectangle.angled")
                        .font(.title)
                        .foregroundColor(.gray)
                }
            }
            .frame(height: 100)
            .frame(maxWidth: .infinity)
            .clipped()

            VStack(alignment: .leading, spacing: 8) {
                Text(route.name)
                    .font(.headline)
                    .foregroundColor(.black)

                Text("Length: \(String(format: "%.2f", route.length)) mi")
                    .font(.subheadline)
                    .foregroundColor(.gray)

                if let distanceMiles {
                    Text("Distance: \(String(format: "%.2f", distanceMiles)) mi")
                        .font(.subheadline)
                        .foregroundColor(.gray)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding()
        }
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.black.opacity(0.08), lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(0.12), radius: 8, x: 0, y: 3)
        .task(id: route.id) {
            if route.imageURL != nil {
                unsplashImageURL = route.imageURL
            } else {
                unsplashImageURL = await UnsplashService.shared.getPhotoURL(for: route.name, category: photoCategory(for: route))
            }
        }
    }
}

struct RouteCard_AllCategories: View {
    @ObservedObject var filterViewModel: FilterViewModel
    @ObservedObject var routeViewModel: RouteViewModel
    @ObservedObject var locationSearch: LocationSearch
    var userId: String?
    var onRouteSelected: ((Route) -> Void)?
    @State private var isLoading = true
    @State private var isLoadingSupplement = false
    @State private var lastScrollOffset: CGFloat = .nan
    @State private var isWeatherSuggestionPresented = false
    @State private var suggestionLocation: CLLocationCoordinate2D? = nil

    /// Routes to display: from RouteViewModel (filtered when user taps "Show"), so filter sheet applies via applyFilter.
    private var displayedRoutes: [Route] {
        routeViewModel.displayedRoutes
    }

    private var filterChangeId: String {
        let f = filterViewModel.currentFilter
        return "\(f.selectedDistance?.rawValue ?? "nil")-\(f.selectedDifficulty?.rawValue ?? "nil")-\(f.selectedSuitability.count)"
    }

    var body: some View {
        ZStack(alignment: .center) {
            VStack(alignment: .leading, spacing: 16) {
                if isLoading {
                    ProgressView("Loading routes…")
                        .frame(maxWidth: .infinity, alignment: .center)
                        .padding()
                } else if isLoadingSupplement {
                    ProgressView("Fetching more routes…")
                        .frame(maxWidth: .infinity, alignment: .center)
                        .padding()
                } else if displayedRoutes.isEmpty {
                    Text(routeViewModel.allRoutes.isEmpty ? "No routes available for this location. Try UCI area or adjust filters." : "No routes match your filters")
                        .foregroundColor(.secondary)
                } else {
                    ScrollViewReader { proxy in
                        HStack(alignment: .firstTextBaseline) {
                            Text("Suggested for you")
                                .font(.title2)
                                .fontWeight(.semibold)
                            Spacer()
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

                                ForEach(displayedRoutes) { route in
                                    RouteCard(
                                        route: route,
                                        userLocation: CLLocation(
                                            latitude: locationSearch.activeLocation.latitude,
                                            longitude: locationSearch.activeLocation.longitude
                                        )
                                    )
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
                        .onAppear { print("[RouteCards] Showing \(displayedRoutes.count) routes in scroll view") }
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

            if isWeatherSuggestionPresented, let loc = suggestionLocation {
                WeatherSuggestionPanel(
                    location: loc,
                    locationName: locationSearch.locationDisplayName,
                    filter: filterViewModel.currentFilter
                )
                    .transition(.opacity.combined(with: .scale))
                    .zIndex(10)
            }
        }
        .frame(minHeight: 0, maxHeight: .infinity)
        .task(id: "\(locationSearch.activeLocation.latitude)-\(locationSearch.activeLocation.longitude)") {
            let (lat, lon) = locationSearch.routeParams()
            let coord = CLLocationCoordinate2D(latitude: lat, longitude: lon)
            await MainActor.run {
                suggestionLocation = coord
                isWeatherSuggestionPresented = true
            }
            let fromAPI = await loadGeoJsonFromAPI(
                latitude: lat,
                longitude: lon,
                userId: userId
            )
            routeViewModel.allRoutes = fromAPI
            routeViewModel.applyFilter(filterViewModel.currentFilter)
            isLoading = false
            await MainActor.run {
                isWeatherSuggestionPresented = false
            }
            print("[RouteCards] Routes loaded: \(fromAPI.count) from API")
            
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

