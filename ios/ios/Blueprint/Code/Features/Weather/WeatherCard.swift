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
                Text("UV index: \(current_weather.current.uvi)").font(.system(size: 13, weight: .medium))
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

    var body: some View {
        GeometryReader { geo in
            let cardWidth = geo.size.width
            let cardHeight = cardWidth / 2.25
            ZStack(alignment: .topLeading) {
                ImageView()
                GradientOverlay(width: cardWidth, height: cardHeight)
                WeatherInfoView(locationSearch: locationSearch).padding(20)
            }
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
