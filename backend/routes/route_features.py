from dataclasses import dataclass

@dataclass(frozen=True)
class RouteFeatures:
    length_m: float
    sidewalk_ratio: float
    lit_ratio: float
    residential_ratio: float
    trail_ratio: float
    paved_ratio: float
    accessible_ratio: float
    steps_ratio: float
    avg_incline: float | None = None

    # scoring functions
    '''
    Urban: ranges from around [-0.2, 0.9]
        -0.2  → hostile / awkward
        0.3  → mixed / inconsistent
        0.6  → comfortable
        0.9+ → very city-friendly
    '''
    @property
    def urban_score(self) -> float:
        score = (0.35 * self.sidewalk_ratio + 0.30 * self.lit_ratio 
                + 0.25 * self.residential_ratio - 0.20 * self.steps_ratio)
        return score

    '''
    Accessibility: ranges from [0,1]
        0.0-0.2  → not accessible
        0.3-0.5  → partially accessible
        0.6-0.8  → mostly accessible
        0.9-1.0  → highly accessible
    '''
    @property
    def accessibility_score(self) -> float:
        score = (0.4 * self.paved_ratio + 0.4 * self.sidewalk_ratio 
                + 0.2 * self.lit_ratio - 0.8 * self.steps_ratio)
        return max(0.0, score)

    '''
    Relaxed walk:
        -0.2 → stressful / effortful
        0.2 → neutral
        0.5 → pleasant
        0.7+ → very relaxed
    '''
    @property
    def relaxed_walk_score(self) -> float:
        score = (0.4 * self.trail_ratio + 0.3 * self.residential_ratio 
                - 0.2 * self.steps_ratio)
        return score

    # For later: add difficulty score?