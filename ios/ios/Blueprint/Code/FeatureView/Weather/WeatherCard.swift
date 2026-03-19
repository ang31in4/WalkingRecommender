//
//  WeatherView.swift
//  ios
//
//  Created by My Meo on 2/11/26.
//

import Foundation
import SwiftUI
internal import _LocationEssentials

struct WeatherInfoView: View {
    @ObservedObject var locationSearch: LocationSearch
    @StateObject private var weatherViewModel = WeatherViewModel()

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            if let current_weather = weatherViewModel.weather {
                Text("Current weather in \(locationSearch.locationDisplayName)")
                    .font(.system(size: 13, weight: .medium))
                Text("Temperature: \(Int(round(current_weather.current.temp)))°F").font(.system(size: 13, weight: .medium))
                Text("Humidity: \(current_weather.current.humidity)").font(.system(size: 13, weight: .medium))
                Text("UV index: \(Int(round(current_weather.current.uvi)))").font(.system(size: 13, weight: .medium))
            }
        }
        .font(.system(size: 11))
        .foregroundColor(.white)
        .padding(.horizontal, 16)
        .padding(.bottom, 16)
        .onAppear {
            let loc = locationSearch.activeLocation
            weatherViewModel.updateLocation(lat: loc.latitude, lon: loc.longitude)
        }
        .onChange(of: locationSearch.activeLocationId) { _, _ in
            let loc = locationSearch.activeLocation
            weatherViewModel.updateLocation(lat: loc.latitude, lon: loc.longitude)
        }
        .onDisappear {
            weatherViewModel.stopRefresh()
        }
    }
}

struct WeatherView: View {
    @ObservedObject var locationSearch: LocationSearch
    @State private var todaySteps: Int = 0

    private func loadSteps() async {
        // Request authorization; if denied, HealthKit queries will return 0.
        _ = await HealthStepService.shared.requestAuthorization()
        todaySteps = await HealthStepService.shared.todayStepCount()
        print("[WeatherView] todaySteps=\(todaySteps)")
    }

    var body: some View {
        GeometryReader { geo in
            let cardWidth = geo.size.width
            let cardHeight = cardWidth / 2.25
            ZStack(alignment: .topLeading) {
                ImageView()
                GradientOverlay(width: cardWidth, height: cardHeight)
                WeatherInfoView(locationSearch: locationSearch).padding(20)

                VStack(spacing: 2) {
                    Image(systemName: "heart.fill")
                        .font(.system(size: 18, weight: .bold))
                        .foregroundColor(.red)
                    Text("\(todaySteps)")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(.white)
                }
                .frame(maxWidth: .infinity, alignment: .topTrailing)
                .padding(.top, 14)
                .padding(.trailing, 14)
            }
            .frame(width: cardWidth, height: cardHeight, alignment: .topLeading)
        }
        .frame(height: UIScreen.main.bounds.width / 2.25)
        .task {
            await loadSteps()
        }
    }
}

struct ImageView: View {
    var body: some View {
        GeometryReader {
            geo in let cardWidth = geo.size.width
            let cardHeight = cardWidth / 2.25
            Image("beautiful-park")
                .resizable()
                .aspectRatio(contentMode: .fill)
                .frame(width: cardWidth, height: cardHeight)
                .clipped()
        }
    }
}

struct GradientOverlay: View {
    let width: CGFloat
    let height: CGFloat
    var opacity: Double = 0.55
    var cornerRadius: CGFloat = 20

    var body: some View {
        LinearGradient(
            colors: [.clear, .black.opacity(opacity)],
            startPoint: .top,
            endPoint: .bottom
        )
        .frame(width: width, height: height)
    }
}
