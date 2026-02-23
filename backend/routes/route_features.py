from dataclasses import dataclass

@dataclass(frozen=True)
class RouteFeatures:
    length_m: float
    sidewalk_ratio: float
    lit_ratio: float
    residential_ratio: float
    major_road_ratio: float
    trail_ratio: float
    paved_ratio: float
    rough_surface_ratio: float
    accessible_ratio: float
    steps_ratio: float
    avg_incline: float | None = None
    dog_friendly_ratio: float

    # scoring functions
    '''
    Urban:
        -0.45  → hostile / awkward
        0.2  → mixed / inconsistent
        0.6  → comfortable
        0.9+ → very city-friendly
    '''
    @property
    def urban_score(self) -> float:
        score = (
            0.35 * self.sidewalk_ratio 
            + 0.30 * self.lit_ratio 
            + 0.25 * self.residential_ratio 
            - 0.20 * self.steps_ratio
            - 0.25 * self.major_road_ratio
        )
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
        score = (
            0.4 * self.paved_ratio 
            + 0.4 * self.sidewalk_ratio 
            + 0.2 * self.lit_ratio 
            - 0.8 * self.steps_ratio
            - 0.5 * self.rough_surface_ratio
        )
        return max(0.0, score)

    '''
    Relaxed walk:
        -0.5 → stressful / effortful
        0.2 → neutral
        0.5 → pleasant
        0.7+ → very relaxed
    '''
    @property
    def relaxed_walk_score(self) -> float:
        score = (
            0.4 * self.trail_ratio 
            + 0.3 * self.residential_ratio 
            - 0.2 * self.steps_ratio
            - 0.3 * self.major_road_ratio
        )
        return score

    '''
    Difficulty:
        0.0 → flat, paved, easy
        0.2 → noticeable effort
        0.6 → moderate workout
        0.8+ → physically demanding
    '''
    @property
    def difficulty_score(self) -> float:
        incline_component = abs(self.avg_incline) if self.avg_incline else 0.0
        
        score = (
            0.5 * self.steps_ratio
            + 0.3 * incline_component
            + 0.2 * self.trail_ratio
            + 0.2 * self.rough_surface_ratio
        )
        return min(1.0, score)
    
    '''
    Safety: takes into account lighting, residential areas, and areas of heavy traffic
    0.0 → feels exposed / traffic-heavy
    0.5 → moderately comfortable
    0.8+ → feels very safe
    '''
    @property
    def safety_score(self) -> float:
        score = (
            0.4 * self.lit_ratio +
            0.3 * self.residential_ratio -
            0.3 * self.major_road_ratio
        )
        return score