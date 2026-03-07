import Foundation
import SwiftUI
import MapKit

struct InputView: View {
    @ObservedObject var locationSearch: LocationSearch
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
        VStack(alignment: .leading, spacing: 0) {
            ZStack(alignment: .topLeading) {
                TextField("Enter your location", text: displayText)
                    .focused($isTextFieldFocused)
                    .onSubmit {
                        locationSearch.performSearch()
                    }

                if locationSearch.isSearching {
                    ProgressView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .background(Color(.systemBackground).opacity(0.8))
                }
            }
            .textFieldStyle(.roundedBorder)

            if isTextFieldFocused && !locationSearch.searchCompletions.isEmpty {
                VStack(alignment: .leading, spacing: 0) {
                    ForEach(Array(locationSearch.searchCompletions.prefix(6).enumerated()), id: \.offset) { _, completion in
                        Button {
                            locationSearch.selectCompletion(completion)
                            isTextFieldFocused = false
                        } label: {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(completion.title)
                                    .font(.subheadline)
                                    .foregroundColor(.primary)
                                if !completion.subtitle.isEmpty {
                                    Text(completion.subtitle)
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                            }
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(.vertical, 10)
                            .padding(.horizontal, 12)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .background(Color(.systemBackground))
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color(.systemGray4), lineWidth: 1)
                )
                .cornerRadius(8)
                .shadow(radius: 4)
                .padding(.top, 4)
            }

            if locationSearch.searchedCoordinate != nil {
                HStack {
                    Image(systemName: "location.fill")
                        .foregroundColor(.blue)
                    Text("Using selected location")
                        .font(.subheadline)
                }
                .padding(.top, 8)
            }
        }
        .padding()
    }
}
