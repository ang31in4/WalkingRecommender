from collections import Counter
from typing import List, Dict

from ..users.user_profile import UserProfile
from ..routes.route_features import RouteFeatures
from ..sessions.search_filters import SearchFilters

# Updates a user's weights based on the chosen route relative to other routes  
def update_profile_from_routes(user:UserProfile, 
                              chosen:RouteFeatures,
                              shown:list[RouteFeatures]) -> UserProfile:
    alpha = 0.5
    
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

"""
Pattern checks based on searches -- pattern checks should run periodically, not after every search
"""

PATTERN_THRESHOLD = 0.7
MIN_EVENTS = 5

# Detect strong dominant behavioral patterns in recent searches.
# Returns a dictionary of learned signals.
def detect_patterns(filters: List[SearchFilters]) -> Dict:
    if len(filters) < MIN_EVENTS:
        return {}

    results = {}

    # Difficulty 
    difficulty_values = [f.difficulty for f in filters if f.difficulty]
    if len(difficulty_values) >= MIN_EVENTS:
        counts = Counter(difficulty_values)
        dominant, freq = counts.most_common(1)[0]
        if freq / len(difficulty_values) >= PATTERN_THRESHOLD:
            results["dominant_difficulty"] = dominant

    # Distance
    distance_values = [f.distance for f in filters if f.distance]
    if len(distance_values) >= MIN_EVENTS:
        counts = Counter(distance_values)
        dominant, freq = counts.most_common(1)[0]
        if freq / len(distance_values) >= PATTERN_THRESHOLD:
            results["dominant_distance"] = dominant

    # Boolean Patterns
    def dominant_true(attr: str):
        values = [getattr(f, attr) for f in filters]
        if len(values) >= MIN_EVENTS:
            true_ratio = sum(values) / len(values)
            if true_ratio >= PATTERN_THRESHOLD:
                return True
        return False

    if dominant_true("wheelchair_access"):
        results["requires_wheelchair"] = True

    if dominant_true("avoid_steps"):
        results["avoid_steps"] = True

    if dominant_true("pet_friendly"):
        results["bringing_dog"] = True

    # Cross Pattern: Easy + Short
    easy_short_count = 0
    valid_pairs = 0

    for f in filters:
        if f.difficulty and f.distance:
            valid_pairs += 1
            if f.difficulty == "easy" and f.distance == "<0.5mi":
                easy_short_count += 1

    if valid_pairs >= MIN_EVENTS:
        if easy_short_count / valid_pairs >= PATTERN_THRESHOLD:
            results["casual_user"] = True

    # Cross Pattern: Difficult + Long
    hard_long_count = 0
    valid_pairs = 0

    for f in filters:
        if f.difficulty and f.distance:
            valid_pairs += 1
            if f.difficulty == "difficult" and f.distance == "1+mi":
                hard_long_count += 1

    if valid_pairs >= MIN_EVENTS:
        if hard_long_count / valid_pairs >= PATTERN_THRESHOLD:
            results["fitness_user"] = True

    return results

# Applies structural and weight updates to user profile based on detected patterns.
def update_user_profile_from_patterns(user: UserProfile, patterns: Dict) -> UserProfile:
    # Difficulty Constraint
    if "dominant_difficulty" in patterns:
        difficulty_map = {
            "easy": 0.3,
            "moderate": 0.6,
            "difficult": None
        }

        user.max_difficulty = difficulty_map[patterns["dominant_difficulty"]]

    # Distance Constraint
    if "dominant_distance" in patterns:
        if patterns["dominant_distance"] == "<0.5mi":
            user.min_length_m = None
            user.max_length_m = 800

        elif patterns["dominant_distance"] == "0.5-1mi":
            user.min_length_m = 800
            user.max_length_m = 1600

        elif patterns["dominant_distance"] == "1+mi":
            user.min_length_m = 1600
            user.max_length_m = None

    # Boolean Hard Constraints
    if patterns.get("requires_wheelchair"):
        user.requires_wheelchair = True
        user.accessibility_weight = min(user.accessibility_weight + 0.2, 2.0)

    if patterns.get("avoid_steps"):
        user.avoid_steps = True
        user.accessibility_weight = min(user.accessibility_weight + 0.1, 2.0)

    if patterns.get("bringing_dog"):
        user.bringing_dog = True
        user.safety_weight = min(user.safety_weight + 0.1, 2.0)

    # Casual User Profile
    if patterns.get("casual_user"):
        user.difficulty_weight = max(user.difficulty_weight - 0.1, 0.0)
        user.safety_weight = min(user.safety_weight + 0.1, 2.0)

    # Fitness User Profile
    if patterns.get("fitness_user"):
        user.difficulty_weight = min(user.difficulty_weight + 0.2, 2.0)
        user.accessibility_weight = max(user.accessibility_weight - 0.1, 0.0)

    return user