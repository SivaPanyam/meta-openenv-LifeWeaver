from dataclasses import dataclass

@dataclass
class WorldState:
    time: str
    current_date: str
    meeting: bool
    family_dinner: bool
    budget: int
    stress: float
    # Dynamic Context Fields
    meeting_priority: str
    dinner_priority: str
    dinner_flexible: bool
    travel_time: int
