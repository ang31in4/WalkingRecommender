from dataclasses import dataclass
from ..routes.route_features import RouteFeatures

@dataclass
class UserProfile:
    user_id: str

    # hard constraints
    requires_wheelchair: bool

    # preferences
    accessibility_weight: float
    urban_weight: float
    relaxed_weight: float
    # add: diffculty weight

    def allowed(self, features:RouteFeatures):
        if self.requires_wheelchair and features.accessibility_score < 0.5:
            return False
        
        return True

    def score(self, features):
        score = ( self.accessibility_weight * features.accessibility_score 
                 + self.urban_weight * features.urban_score 
                 + self.relaxed_weight * features.relaxed_walk_score )
        
        return score