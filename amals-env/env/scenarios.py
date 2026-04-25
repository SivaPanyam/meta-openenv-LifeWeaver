import random
from .world import WorldState

def generate_schedule_conflict():
    """Generates a dynamic, randomized schedule conflict scenario."""
    priorities = ["low", "medium", "high"]
    
    return WorldState(
        time="evening",
        meeting=True,
        family_dinner=True,
        # Dynamic context
        meeting_priority=random.choice(priorities),
        dinner_priority=random.choice(priorities),
        dinner_flexible=random.choice([True, False]),
        travel_time=random.randint(0, 60),
        budget=random.randint(500, 3000),
        stress=round(random.uniform(0.3, 0.9), 2)
    )
