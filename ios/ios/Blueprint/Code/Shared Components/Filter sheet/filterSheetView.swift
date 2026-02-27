import Foundation
import SwiftUI

struct FilterButtonView: View {
    @ObservedObject var filterViewModel: FilterViewModel

    var body: some View {
        Button("Filter") {
            filterViewModel.showFilterSheet()
        }
        .padding(.horizontal)
        .padding(.vertical, 10)
        .background(Color.green)
        .foregroundStyle(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: 5))
    }
}

private struct FilterCheckboxRow: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack {
                Text(title)
                    .foregroundColor(.primary)
                Spacer()
                Image(systemName: isSelected ? "checkmark.square.fill" : "square")
                    .foregroundColor(isSelected ? Color.green : Color.gray)
            }
            .padding(.vertical, 12)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }
}

struct FilterSheetView: View {
    @ObservedObject var filterViewModel: FilterViewModel

    private let limeGreen = Color(red: 0.56, green: 0.93, blue: 0.56)

    var body: some View {
        VStack(spacing: 0) {

            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    VStack(alignment: .leading, spacing:8) {
                        Text("Difficulty")
                            .font(.headline)
                            .fontWeight(.bold)
                        ForEach(RouteDifficulty.allCases, id: \.self) { difficulty in
                            FilterCheckboxRow(
                                title: difficulty.displayName,
                                isSelected: filterViewModel.currentFilter.selectedDifficulty == difficulty
                            ) {
                                filterViewModel.setDifficulty(difficulty)
                            }
                        }
                    }

                    VStack(alignment: .leading, spacing: 8) {
                        Text("Distances")
                            .font(.headline)
                            .fontWeight(.bold)
                        ForEach(DistanceRange.allCases, id: \.self) { distance in
                            FilterCheckboxRow(
                                title: distance.displayName,
                                isSelected: filterViewModel.currentFilter.selectedDistance == distance
                            ) {
                                filterViewModel.setDistance(distance)
                            }
                        }
                    }

                    VStack(alignment: .leading, spacing: 8) {
                        Text("Suitability")
                            .font(.headline)
                            .fontWeight(.bold)
                        ForEach(Suitability.allCases, id: \.self) { suitability in
                            FilterCheckboxRow(
                                title: suitability.displayName,
                                isSelected: filterViewModel.currentFilter.selectedSuitability.contains(suitability)
                            ) {
                                filterViewModel.setSuitability(
                                    suitability,
                                    selected: !filterViewModel.currentFilter.selectedSuitability.contains(suitability)
                                )
                            }
                        }
                    }
                }
                .padding(20)
            }

            HStack(spacing: 12) {
                Button("Clear") {
                    filterViewModel.clearFilters()
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 14)
                .background(limeGreen)
                .foregroundStyle(.white)
                .fontWeight(.semibold)
                .clipShape(RoundedRectangle(cornerRadius: 10))

                Button("Show") {
                    filterViewModel.applyFilter()
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 14)
                .background(limeGreen)
                .foregroundStyle(.white)
                .fontWeight(.semibold)
                .clipShape(RoundedRectangle(cornerRadius: 10))
            }
            .padding(20)
            .background(Color(.systemBackground))
        }
        .background(Color(.systemGroupedBackground))
    }
}



