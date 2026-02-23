//
//  WeatherView.swift
//  ios
//
//  Created by My Meo on 2/11/26.
//

import Foundation
import SwiftUI

struct WeatherInfoView: View {
    @StateObject var weatherViewModel = WeatherViewModel()
    
    var body: some View {
        VStack (alignment: .leading, spacing: 4) {
            if let current_weather = weatherViewModel.weather{
                Text("Current weather in Irvine").font(.system(size: 13, weight: .medium))
                Text("Temperature: \(current_weather.current.temp)").font(.system(size: 13, weight: .medium))
                Text("Humidity: \(current_weather.current.humidity)").font(.system(size: 13, weight: .medium))
                Text("UV index: \(current_weather.current.uvi)").font(.system(size: 13, weight: .medium))
            }
        }
        .font(.system(size: 11))
        .foregroundColor(.white)
        .padding(.horizontal, 16)
        .padding(.bottom, 16)
        .onAppear() {
            weatherViewModel.fetchWeather()
        }
    }
}

struct WeatherView: View {
    var body: some View {
        GeometryReader {
            geo in let cardWidth = geo.size.width
            let cardHeight = cardWidth / 1.95
            ZStack (alignment: .bottomLeading){
                ImageView()
                GradientOverlay(width:cardWidth, height: cardHeight)
                WeatherInfoView()
            }
            .frame(width: cardWidth, height:cardHeight)
        }
    }
}

struct ImageView: View {
    var body: some View {
        GeometryReader {
            geo in let cardWidth = geo.size.width
            let cardHeight = cardWidth / 1.95
            Image("beautiful-park")
                .resizable()
                .aspectRatio(contentMode: .fill)
                .frame(width: cardWidth, height: cardHeight)
                .clipped()
                .cornerRadius(15)
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
        .cornerRadius(cornerRadius)
    }
}
