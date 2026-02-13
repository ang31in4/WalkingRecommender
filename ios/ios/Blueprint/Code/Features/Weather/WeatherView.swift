//
//  WeatherView.swift
//  ios
//
//  Created by My Meo on 2/11/26.
//

import Foundation
import SwiftUI

struct WeatherView: View {
    @StateObject var weatherViewModel = WeatherViewModel()
    
    var body: some View {
        VStack {
            if let current_weather = weatherViewModel.weather{
                Text("Current weather in Irvine").font(.title).padding()
                Text("Temperature: \(current_weather.current.temp)").font(.title).padding()
                Text("Humidity: \(current_weather.current.humidity)").font(.title).padding()
                Text("UV index: \(current_weather.current.uvi)").font(.title).padding()
            }
        }
        .padding()
        .onAppear() {
            weatherViewModel.fetchWeather()
        }
    }
}
