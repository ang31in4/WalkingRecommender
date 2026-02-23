from dataclasses import dataclass
from ..routes.route_features import RouteFeatures

@dataclass
class UserProfile:
    user_id: str

    # hard constraints
    requires_wheelchair: bool
    max_difficulty: float | None = None

    # preferences
    accessibility_weight: float
    urban_weight: float
    relaxed_weight: float
    difficulty_weight: float

    def allowed(self, features:RouteFeatures):
        if self.requires_wheelchair and features.accessibility_score < 0.5:
            return False
        if self.max_difficulty is not None and features.difficulty_score > self.max_difficulty:
            return False
        
        return True

    def score(self, features):
        score = ( 
            self.accessibility_weight * features.accessibility_score 
            + self.urban_weight * features.urban_score 
            + self.relaxed_weight * features.relaxed_walk_score 
            - self.difficulty_weight * features.difficulty_score
        )
        
        return score