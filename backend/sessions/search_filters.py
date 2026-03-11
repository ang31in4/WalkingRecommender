from dataclasses import dataclass

@dataclass
class SearchFilters:
    difficulty: str | None      # "easy", "moderate", "difficult"
    distance: str | None        # "<0.5mi", "0.5-1mi", "1+mi"

    wheelchair_access: bool
    # avoid_steps: bool
    pet_friendly: bool
    urban: bool  # prefer urban routes; scoring uses user's urban_weight