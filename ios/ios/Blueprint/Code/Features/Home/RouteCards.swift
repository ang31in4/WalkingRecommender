import Foundation
import SwiftUI

struct RouteCard: View {
    let route: Route

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(route.name)
                .font(.headline)
                .foregroundColor(.primary)
            Text(String(format: "%.2f mi", route.length))
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .frame(height: 100)
        .background(Color.blue.opacity(0.3))
        .cornerRadius(10)
        .shadow(color: Color.black.opacity(0.1), radius: 5)
    }
}

struct RouteCard_SameCategory: View {
    let title: String
    let route: Route

    var body: some View {
        VStack(alignment: .leading) {
            Text(title)
                .font(.title2)
                .fontWeight(.semibold)
            HStack {
                ForEach(1...3, id: \.self) { _ in
                    RouteCard(route: route)
                }
            }
        }
    }
}

struct RouteCard_AllCategories: View {
    private let routes = loadGeoJson()

    var body: some View {
        VStack(alignment: .leading, spacing: 24) {
            if let route = routes.first {
                RouteCard_SameCategory(title: "Top paths nearby", route: route)
                RouteCard_SameCategory(title: "5000 steps Blitz", route: route)
                RouteCard_SameCategory(title: "A traffic-free zone", route: route)
            } else {
                Text("No routes available")
                    .foregroundColor(.secondary)
            }
        }
    }
}

