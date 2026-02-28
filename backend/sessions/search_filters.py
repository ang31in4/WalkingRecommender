from dataclasses import dataclass

@dataclass
class SearchFilters:
    difficulty: str | None
    distance: str | None

    wheelchair_access: bool
    avoid_steps: bool

    pet_friendly: bool