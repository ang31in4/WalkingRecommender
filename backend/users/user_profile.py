from dataclasses import dataclass
from ..routes.route_features import RouteFeatures

@dataclass
class UserProfile:
    user_id: str

    # hard constraints
    requires_wheelchair: bool
    avoid_steps: bool
    
    min_length_m: float | None
    max_length_m: float | None
    max_difficulty: float | None
    
    bringing_dog: bool

    # preference weights
    accessibility_weight: float
    urban_weight: float
    relaxed_weight: float
    difficulty_weight: float
    safety_weight:  float

    def allowed(self, features:RouteFeatures):
        # mobility
        if self.requires_wheelchair:
            if features.accessibility_score < 0.5:
                return False
            if features.steps_ratio > 0:
                return False
        
        if self.avoid_steps and features.steps_ratio > 0:
            return False
        
        # distance
        if self.min_length_m is not None:
            if features.length_m < self.min_length_m:
                return False

        if self.max_length_m is not None:
            if features.length_m > self.max_length_m:
                return False

        # difficulty
        if self.max_difficulty is not None:
            if features.difficulty_score > self.max_difficulty:
                return False
        
        # dog constraint
        if self.bringing_dog:
            if features.dog_friendly_ratio < 0.7:
                return False
        
        return True

    def score(self, features):
        score = ( 
            self.accessibility_weight * features.accessibility_score 
            + self.urban_weight * features.urban_score 
            + self.relaxed_weight * features.relaxed_walk_score 
            + self.safety_weight * features.safety_score
            - self.difficulty_weight * features.difficulty_score
        )
        
        return score
    
    def normalize_weights(self):
        total = (
            self.accessibility_weight +
            self.urban_weight +
            self.relaxed_weight +
            self.difficulty_weight +
            self.safety_weight
        )

        if total == 0:
            return

        self.accessibility_weight /= total
        self.urban_weight /= total
        self.relaxed_weight /= total
        self.difficulty_weight /= total
        self.safety_weight /= total