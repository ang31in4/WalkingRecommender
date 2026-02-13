import Foundation
import SwiftUI

struct RouteCard: View {
    var body: some View {
        Rectangle()
            .fill(Color.blue)
            .frame(height: 100)
            .cornerRadius(10)
            .shadow(color: Color.black.opacity(0.1), radius: 5)
            .frame(maxWidth: .infinity)
    }
}

struct RouteCard_SameCategory : View {
    let title: String
    var body: some View {
        VStack {
            Text(title)
            HStack {
                ForEach(1...3, id: \.self) { index in
                    RouteCard()
                }
            }
        }
    }
}

struct RouteCard_AllCategories: View {
    var body: some View {
        VStack {
            RouteCard_SameCategory(title: "Top paths nearby")
            RouteCard_SameCategory(title: "5000 steps Blitz")
            RouteCard_SameCategory(title: "A traffic-free zone")
        }
    }
}

