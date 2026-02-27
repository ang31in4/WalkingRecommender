import SwiftUI
import Combine

struct ContentView: View {
    @StateObject private var filterViewModel = FilterViewModel()

    var body: some View {
        VStack {
//            WeatherView()
            HStack(alignment: .center) {
                InputView()
                FilterButtonView(filterViewModel: filterViewModel)
            }
            RouteCard_AllCategories()
        }
        .padding(20)
        .sheet(isPresented: $filterViewModel.isFilterSheetPresented) {
            FilterSheetView(filterViewModel: filterViewModel)
        }
    }
}

#Preview {
    ContentView()
}
