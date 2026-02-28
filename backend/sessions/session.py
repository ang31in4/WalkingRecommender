from dataclasses import dataclass
from datetime import datetime
from .search_filters import SearchFilters

@dataclass
class SearchSession:
    session_id: int | None
    user_id: str
    timestamp: datetime

    selected_filters: SearchFilters