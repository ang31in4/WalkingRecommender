import Foundation
import UIKit

class UnsplashService {
    
    static let shared = UnsplashService()
    private init() {}
    
    // Cache to avoid fetching same image multiple times
    private var imageCache: [String: String] = [:]
    
    func getPhotoURL(for routeName: String, category: PhotoCategory = .trail) async -> String? {
        let cacheKey = "\(routeName)_\(category.rawValue)"
        if let cachedURL = imageCache[cacheKey] {
            return cachedURL
        }
        
        let query = buildQuery(routeName: routeName, category: category)
        let base = UnsplashAPIConfig.baseURL
        let accessKey = UnsplashAPIConfig.unsplashAccessKey
        
        guard let encodedQuery = query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed),
              let url = URL(string: "\(base)/search/photos?query=\(encodedQuery)&per_page=1&client_id=\(accessKey)") else {
            return nil
        }
        
        do {
            let (data, response) = try await URLSession.shared.data(from: url)
            
            guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
                print("Unsplash API error: \((response as? HTTPURLResponse)?.statusCode ?? -1)")
                return nil
            }
            
            let decoder = JSONDecoder()
            let searchResult = try decoder.decode(UnsplashSearchResponse.self, from: data)
            
            guard let photoURL = searchResult.results.first?.urls.regular else {
                return nil
            }
            
            imageCache[cacheKey] = photoURL
            print("Sucessfully fetched photo URL at \(routeName)")
            
            return photoURL
            
        } catch {
            print("Unsplash fetch error: \(error)")
            return nil
        }
    }
    
    private func buildQuery(routeName: String, category: PhotoCategory) -> String {
        let baseTerms = category.searchTerms
        // Extract location hints from route name if possible
        let cleanName = routeName.replacingOccurrences(of: "Trail", with: "")
                                  .replacingOccurrences(of: "Loop", with: "")
                                  .trimmingCharacters(in: .whitespaces)
        
        return "\(cleanName) \(baseTerms)"
    }
}

// MARK: - Photo Categories
enum PhotoCategory: String {
    case trail = "trail"
    case park = "park"
    case urban = "urban"
    case nature = "nature"
    
    var searchTerms: String {
        switch self {
        case .trail:
            return "hiking trail path nature outdoor"
        case .park:
            return "park walking path green trees"
        case .urban:
            return "city street walking urban pathway"
        case .nature:
            return "nature outdoor scenic landscape"
        }
    }
}

// MARK: - Models
struct UnsplashSearchResponse: Decodable {
    let results: [UnsplashPhoto]
}

struct UnsplashPhoto: Decodable {
    let id: String
    let urls: UnsplashURLs
}

struct UnsplashURLs: Decodable {
    let raw: String
    let full: String
    let regular: String
    let small: String
    let thumb: String
}
