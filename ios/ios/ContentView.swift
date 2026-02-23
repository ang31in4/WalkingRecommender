import SwiftUI
import Combine

struct ContentView: View {
    var body: some View {
        VStack {
//            WeatherView()
            InputView()
            RouteCard_AllCategories()
        }
        .padding(20)
    }
}

#Preview {
    ContentView()
}
