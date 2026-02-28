from ..users.user_profile import UserProfile
from ..routes.route_features import RouteFeatures

# updates a user's weights based on the chosen route relative to other routes  
def update_profile_from_routes(user:UserProfile, 
                              chosen:RouteFeatures,
                              shown:list[RouteFeatures],
                              alpha: float=0.5) -> UserProfile:
    mean_features = {
        "urban": sum(r.urban_score for r in shown) / len(shown),
        "accessibility": sum(r.accessibility_score for r in shown) / len(shown),
        "difficulty": sum(r.difficulty_score for r in shown) / len(shown),
        "safety": sum(r.safety_score for r in shown) / len(shown)
    }

    differences = {
        "urban": chosen.urban_score - mean_features["urban"],
        "accessibility": chosen.accessibility_score - mean_features["accessibility"],
        "difficulty": chosen.difficulty_score - mean_features["difficulty"],
        "safety": chosen.safety_score - mean_features["safety"]
    }

    user.urban_weight += alpha * differences["urban"]
    user.accessibility_weight += alpha * differences["accessibility"]
    user.difficulty_weight += alpha * differences["difficulty"]
    user.safety_weight += alpha * differences["safety"]

    user.normalize_weights()

    return user

