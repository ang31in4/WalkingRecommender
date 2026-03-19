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
    case postUserSteps(userId: String)
    case getUserStepGoal(userId: String)

    var urlString: String {
        let base = APIConfig.baseURL
        switch self {
        case .login:
            return "\(base)/api/login"
        case .getRoutes:
            return "\(base)/api/routes"
        case .postRouteSelected:
            return "\(base)/api/session/route_selected"
        case .postUserSteps(let userId):
            let encoded = userId.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? userId
            return "\(base)/api/user/\(encoded)/steps"
        case .getUserStepGoal(let userId):
            let encoded = userId.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? userId
            return "\(base)/api/user/\(encoded)/step_goal"
        }
    }

    var method: HttpMethod {
        switch self {
        case .login: return .POST
        case .getRoutes: return .POST
        case .postRouteSelected: return .POST
        case .postUserSteps: return .POST
        case .getUserStepGoal: return .GET
        }
    }
}
