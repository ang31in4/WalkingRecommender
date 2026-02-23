import Foundation
import SwiftUI

struct InputView: View {
    @StateObject var locationSearch = LocationSearch()
    
    var body: some View {
        VStack {
            TextField("Enter your location", text: $locationSearch.searchText).onSubmit {
                locationSearch.performSearch()
            }
            if locationSearch.searchedCoordinate != nil {
                HStack {
                    Image(systemName: "location.fill")
                        .foregroundColor(.blue)
                    Text("Using current location")
                        .font(.subheadline)
                }
                .padding(.top, 5)
            }
            if locationSearch.currentCoordinate != nil {
                Text("Finding your location...")
                    .font(.caption)
                    .foregroundColor(.gray)
            } else {
                Text("You are at UCI" )
            }
        }
        .textFieldStyle(.roundedBorder)
        .padding()
    }
}
