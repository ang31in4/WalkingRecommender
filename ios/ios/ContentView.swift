import SwiftUI
import Combine

struct ContentView: View {
    @StateObject private var loginViewModel = LoginViewModel()
    @StateObject private var filterViewModel = FilterViewModel()

    var body: some View {
        Group {
            if loginViewModel.isLoggedIn {
                HomeView(loginViewModel: loginViewModel)
            } else {
                LoginScreen(viewModel: loginViewModel)
            }
        }
    }
}

struct HomeView: View {
    @StateObject private var locationSearch = LocationSearch()
    @StateObject private var filterViewModel = FilterViewModel()
    @StateObject private var routeViewModel = RouteViewModel()
    @ObservedObject var loginViewModel: LoginViewModel
    @State private var selectedRoute: Route?

    var body: some View {
        GeometryReader { geo in
            let headerH = geo.size.width / 2.25
            VStack(spacing: 0) {
                WeatherView(locationSearch: locationSearch)
                    .frame(height: headerH)
                    .overlay(alignment: .bottom) {
                        HStack(alignment: .center) {
                            // Allow InputView to grow so autocomplete appears below the text field.
                            InputView(locationSearch: locationSearch)
                                .frame(height: 44)
                            FilterButtonView(filterViewModel: filterViewModel)
                                .font(.caption)
                        }
                        .padding(20)
                    }
                    // Keep the weather/input overlay above the route list.
                    .zIndex(2)
                
                RouteCard_AllCategories(
                    filterViewModel: filterViewModel,
                    routeViewModel: routeViewModel,
                    locationSearch: locationSearch,
                    userId: loginViewModel.userId,
                    onRouteSelected: { selectedRoute = $0 }
                )
                .zIndex(1)
                .frame(height: max(0, geo.size.height - headerH))
                .padding(.horizontal, 30)
                .padding(.vertical, 8)
            }
            .frame(width: geo.size.width, height: geo.size.height, alignment: .top)
        }
        .ignoresSafeArea(.keyboard)
        .safeAreaInset(edge: .bottom) {
            HStack {
                Spacer()
                Button("Logout") {
                    loginViewModel.logout()
                }
                .padding(.horizontal)
                .padding(.vertical, 10)
                .background(Color.green)
                .foregroundStyle(Color.white)
                .clipShape(RoundedRectangle(cornerRadius: 5))
                Spacer()
            }
            .padding(.vertical, 12)
        }
        .onAppear {
            filterViewModel.onApplyFilter = { [routeViewModel] filter in
                routeViewModel.applyFilter(filter)
            }
        }
        .sheet(isPresented: $filterViewModel.isFilterSheetPresented) {
            FilterSheetView(filterViewModel: filterViewModel, userId: loginViewModel.userId)
        }
        .sheet(item: $selectedRoute) { route in
            NavigationStack {
                RouteMapScreen(route: route, onStart: {
                    performRouteSelection(userId: loginViewModel.userId, route: route)
                })
                .ignoresSafeArea(edges: .bottom)
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Done") { selectedRoute = nil }
                    }
                    ToolbarItem(placement: .primaryAction) {
                        Button("Select") {
                            performRouteSelection(userId: loginViewModel.userId, route: route)
                        }
                    }
                }
            }
        }
    }

    private func performRouteSelection(userId: String, route: Route) {
        guard !userId.isEmpty else { return }
        Task {
            _ = await HealthStepService.shared.requestAuthorization()
            let steps = await HealthStepService.shared.todayStepCount()
            _ = try? await postRouteSelected(userId: userId, route: route)
            _ = try? await postUserSteps(userId: userId, currentSteps: steps)
            if let goal = try? await getUserStepGoal(userId: userId) {
                print("[Steps] current_step=\(goal.current_step ?? -1), step_goal=\(goal.step_goal ?? -1)")
            } else {
                print("[Steps] current_step/step_goal fetch failed for user=\(userId)")
            }
            await MainActor.run { selectedRoute = nil }
        }
    }
}

#Preview {
    ContentView()
}
