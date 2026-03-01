import Foundation
import SwiftUI

struct InputView: View {
    @StateObject var locationSearch = LocationSearch()
    @FocusState private var isTextFieldFocused: Bool

    private var displayText: Binding<String> {
        Binding(
            get: {
                if !locationSearch.searchText.isEmpty {
                    return locationSearch.searchText
                }
                if isTextFieldFocused {
                    return ""
                }
                return locationSearch.currentCoordinate != nil ? "Current location" : "UCI"
            },
            set: { locationSearch.searchText = $0 }
        )
    }

    var body: some View {
        VStack {
            TextField("Enter your location", text: displayText)
                .focused($isTextFieldFocused)
                .onSubmit {
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
        }
        .textFieldStyle(.roundedBorder)
        .padding()
    }
}
