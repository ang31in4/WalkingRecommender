import SwiftUI
import MapKit

// MARK: - Route map screen (header + map + Start button)

struct RouteMapScreen: View {
    let route: Route
    var onStart: (() -> Void)?

    private var estimatedMinutes: Int {
        let walkingMinutesPerMile = 18.0
        return max(1, Int(route.length * walkingMinutesPerMile))
    }

    private var tagLabels: [String] {
        var labels: [String] = []
        let diff = route.difficulty.lowercased()
        if diff == "easy" { labels.append("Easy") }
        else if diff == "moderate" || diff == "medium" { labels.append("Medium") }
        else if diff == "hard" || diff == "difficult" { labels.append("Hard") }
        else { labels.append(route.difficulty.capitalized) }
        if route.petFriendly == true { labels.append("pet friendly") }
        if route.wheelchairAccessible == true { labels.append("wheelchair accessible") }
        if route.urban == true { labels.append("urban") }
        return labels
    }

    var body: some View {
        VStack(spacing: 0) {
            // Translucent header with route info and tags
            VStack(alignment: .leading, spacing: 10) {
                Text(route.name)
                    .font(.headline)
                    .foregroundColor(.primary)
                HStack(spacing: 16) {
                    Text("Length: \(route.length >= 1 ? String(format: "%.0f", route.length) : String(format: "%.2f", route.length)) mile\(route.length == 1 ? "" : "s")")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    Text("Total time: \(estimatedMinutes) min")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(tagLabels, id: \.self) { tag in
                            Text(tag)
                                .font(.caption)
                                .fontWeight(.medium)
                                .padding(.horizontal, 12)
                                .padding(.vertical, 6)
                                .background(Color(.green).opacity(0.8))
                                .foregroundColor(.white)
                                .clipShape(Capsule())
                        }
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding()
            .background(.ultraThinMaterial)

            RouteMapView(route: route)
                .frame(maxWidth: .infinity, maxHeight: .infinity)

            Button(action: { onStart?() }) {
                Text("Start")
                    .fontWeight(.semibold)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
                    .background(Color.green)
                    .foregroundColor(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 24)
            .padding(.top, 12)
        }
        .background(Color(.systemGroupedBackground))
    }
}

// MARK: - Preview (no backend)

#Preview("Map view") {
    RouteMapScreen(route: Route.sample, onStart: {})
}

// MARK: - Map view (MKMapView + polyline)

final class RouteMapViewDelegate: NSObject, MKMapViewDelegate {
    func mapView(_ mapView: MKMapView, rendererFor overlay: MKOverlay) -> MKOverlayRenderer {
        if let polyline = overlay as? MKPolyline {
            let renderer = MKPolylineRenderer(polyline: polyline)
            renderer.strokeColor = .systemBlue
            renderer.lineWidth = 4
            return renderer
        }
        return MKOverlayRenderer(overlay: overlay)
    }
}

struct RouteMapView: UIViewRepresentable {
    let route: Route

    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    func makeUIView(context: Context) -> MKMapView {
        let mapView = MKMapView()
        mapView.delegate = context.coordinator

        let polyline = route.asPolyline()
        mapView.addOverlay(polyline)
        mapView.setVisibleMapRect(
            polyline.boundingMapRect,
            edgePadding: UIEdgeInsets(top: 40, left: 40, bottom: 40, right: 40),
            animated: false
        )

        return mapView
    }

    func updateUIView(_ mapView: MKMapView, context: Context) {
        mapView.removeOverlays(mapView.overlays)
        let polyline = route.asPolyline()
        mapView.addOverlay(polyline)
        mapView.setVisibleMapRect(
            polyline.boundingMapRect,
            edgePadding: UIEdgeInsets(top: 40, left: 40, bottom: 40, right: 40),
            animated: true
        )
    }

    final class Coordinator: NSObject, MKMapViewDelegate {
        private let rendererDelegate = RouteMapViewDelegate()

        func mapView(_ mapView: MKMapView, rendererFor overlay: MKOverlay) -> MKOverlayRenderer {
            rendererDelegate.mapView(mapView, rendererFor: overlay)
        }
    }
}
