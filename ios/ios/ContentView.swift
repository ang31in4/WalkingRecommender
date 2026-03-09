import SwiftUI
import Combine

struct ContentView: View {
    @StateObject private var loginViewModel = LoginViewModel()
    @StateObject private var filterViewModel = FilterViewModel()

    var body: some View {
        Group {
            if loginViewModel.isLoggedIn {
                HomeView(filterViewModel: filterViewModel, loginViewModel: loginViewModel)
            } else {
                LoginScreen(viewModel: loginViewModel)
            }
        }
        .sheet(isPresented: $filterViewModel.isFilterSheetPresented) {
            FilterSheetView(filterViewModel: filterViewModel, userId: loginViewModel.userId)
        }
    }
}

struct HomeView: View {
    @StateObject private var locationSearch = LocationSearch()
    @ObservedObject var filterViewModel: FilterViewModel
    @ObservedObject var loginViewModel: LoginViewModel
    @State private var selectedRoute: Route?

    var body: some View {
        VStack {
            WeatherView(locationSearch: locationSearch)
            HStack(alignment: .center) {
                InputView(locationSearch: locationSearch)
                FilterButtonView(filterViewModel: filterViewModel)
                .font(.caption)
            }
            .padding(20)
            RouteCard_AllCategories(
                filterViewModel: filterViewModel,
                locationSearch: locationSearch,
                userId: loginViewModel.userId,
                onRouteSelected: { selectedRoute = $0 }
            )
            .padding(30)
            Button("Logout") {
                loginViewModel.logout()
            }
        }
        .sheet(item: $selectedRoute) { route in
            NavigationStack {
                RouteMapView(route: route)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .ignoresSafeArea(edges: .bottom)
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Done") { selectedRoute = nil }
                    }
                    ToolbarItem(placement: .primaryAction) {
                        Button("Select") {
                            guard let uid = loginViewModel.userId else { return }
                            Task {
                                _ = try? await postRouteSelected(userId: uid, route: route)
                                await MainActor.run { selectedRoute = nil }
                            }
                        }
                    }
                }
            }
        }
    }
}

#Preview {
    ContentView()
}
