import Foundation
import CoreLocation

enum HttpMethod: String {
    case GET
    case POST
}

enum APIEndpoints {
    case login
    case getRoutes
    case postRouteSelected

    var urlString: String {
        let base = APIConfig.baseURL
        switch self {
        case .login:
            return "\(base)/api/login"
        case .getRoutes:
            return "\(base)/api/routes"
        case .postRouteSelected:
            return "\(base)/api/session/route_selected"
        }
    }

    var method: HttpMethod {
        switch self {
        case .login: return .POST
        case .getRoutes: return .GET
        case .postRouteSelected: return .POST
        }
    }
}
