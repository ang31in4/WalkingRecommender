from dataclasses import dataclass
from ..routes.route_features import RouteFeatures

@dataclass
class UserProfile:
    user_id: str

    # step count data
    current_steps: int
    step_goal: int | None
    step_length_m: int

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
    difficulty_weight: float
    safety_weight:  float
    step_goal_weight: float | None

    def allowed(self, features:RouteFeatures):
        # mobility
        if self.requires_wheelchair:
            if features.accessibility_score < 0.5:
                return False
            if features.steps_ratio > 0:
                return False
        
        if self.avoid_steps and features.steps_ratio > 0:
            return False
        
        return True
    
    def difficulty_penalty(self, difficulty, max_difficulty):
        if max_difficulty is None:
            return 1.0

        if difficulty <= max_difficulty:
            return 1.0

        excess = difficulty - max_difficulty
        return max(0.0, 1 - 2 * excess)

    def step_goal_factor(self, route_distance, remaining_distance):
        if remaining_distance <= 0:
            return 0.5

        if route_distance >= remaining_distance:
            return 1.0  # strong reward for finishing goal

        # otherwise prefer closer matches
        return route_distance / remaining_distance
    
    def score(self, route_features):
        base_score = (
            self.accessibility_weight * route_features.accessibility_score
            + self.urban_weight * route_features.urban_score
            + self.difficulty_weight * route_features.difficulty_score
            + self.safety_weight * route_features.safety_score
        )

        # Difficulty penalty
        difficulty_factor = self.difficulty_penalty(
            route_features.difficulty_score,
            self.max_difficulty
        )

        # Step goal factor
        step_factor = 0.0
        if self.step_goal:
            remaining_steps = max(0, self.step_goal - self.current_steps)
            remaining_distance = remaining_steps * self.step_length_m
            step_factor = self.step_goal_factor(route_features.length_m, remaining_distance)

        return base_score * difficulty_factor * (1 + self.step_goal_weight * step_factor)
    
    def normalize_weights(self):
        total = (
            self.accessibility_weight +
            self.urban_weight +
            self.difficulty_weight +
            self.safety_weight
        )

        if total == 0:
            return

        self.accessibility_weight /= total
        self.urban_weight /= total
        self.difficulty_weight /= total
        self.safety_weight /= total