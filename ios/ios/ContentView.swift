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
            FilterSheetView(filterViewModel: filterViewModel)
        }
    }
}

struct HomeView: View {
    @StateObject private var locationSearch = LocationSearch()
    @ObservedObject var filterViewModel: FilterViewModel
    @ObservedObject var loginViewModel: LoginViewModel

    var body: some View {
        VStack {
            WeatherView(locationSearch: locationSearch)
            HStack(alignment: .center) {
                InputView(locationSearch: locationSearch)
                FilterButtonView(filterViewModel: filterViewModel)
                .font(.caption)
            }
            .padding(20)
            RouteCard_AllCategories(filterViewModel: filterViewModel, locationSearch: locationSearch, userId: loginViewModel.userId)
                .padding(30)
            Button("Logout") {
                loginViewModel.logout()
            }
        }
    }
}

#Preview {
    ContentView()
}
