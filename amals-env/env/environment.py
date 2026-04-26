import random
import copy
from datetime import datetime, timedelta
from .scenarios import generate_schedule_conflict
from .reward import calculate_reward
from mcp_local.calendar_server import CalendarServer

# --- Domain Definitions ---

PROFESSIONAL_POOL = [
    {"type": "team_meeting", "priority": "high", "flexible": False},
    {"type": "client_call", "priority": "high", "flexible": False},
    {"type": "project_sync", "priority": "medium", "flexible": False},
    {"type": "presentation", "priority": "high", "flexible": False},
    {"type": "code_review", "priority": "medium", "flexible": True},
    {"type": "deep_work", "priority": "medium", "flexible": True}
]

PERSONAL_POOL = [
    {"type": "family_dinner", "priority": "high", "flexible": True},
    {"type": "gym", "priority": "medium", "flexible": True},
    {"type": "friend_hangout", "priority": "low", "flexible": True},
    {"type": "personal_errand", "priority": "low", "flexible": True},
    {"type": "hobby_time", "priority": "medium", "flexible": True},
    {"type": "doctor_appt", "priority": "high", "flexible": False}
]

def generate_domain_events(domain_type, count, base_date):
    pool = PROFESSIONAL_POOL if domain_type == "professional" else PERSONAL_POOL
    selected = [copy.deepcopy(e) for e in random.sample(pool, k=min(count, len(pool)))]
    for e in selected:
        e["domain"] = domain_type
        e["date"] = base_date.strftime("%Y-%m-%d")
        e["source"] = random.choice(["email", "calendar"]) if domain_type == "professional" else random.choice(["conversation", "manual"])
    return selected

def assign_realistic_time(events):
    for event in events:
        if event["domain"] == "professional":
            hour = random.randint(9, 17)
        else:
            # Personal: 6-8 or 18-21
            hour = random.choice([random.randint(6, 8), random.randint(18, 21)])
        minute = random.choice(["00", "30"])
        event["time"] = f"{hour:02d}:{minute}"
        event["duration"] = random.choice([30, 60, 90])
    return events

def get_minutes(time_str):
    h, m = map(int, time_str.split(":"))
    return h * 60 + m

def generate_all_events(base_date):
    """Enhanced generation with complex conflicts and dates."""
    events = generate_domain_events("professional", random.randint(2, 3), base_date)
    events += generate_domain_events("personal", random.randint(2, 3), base_date)
    
    random.shuffle(events)
    assign_realistic_time(events)

    has_conflict = False
    # 35% chance to force a conflict (within same domain to respect time rules)
    if random.random() < 0.35:
        if len(events) >= 2:
            # Try to find two events in the same domain to conflict
            prof_events = [i for i, e in enumerate(events) if e["domain"] == "professional"]
            pers_events = [i for i, e in enumerate(events) if e["domain"] == "personal"]
            
            target_indices = None
            if len(prof_events) >= 2 and random.random() < 0.7:
                target_indices = random.sample(prof_events, 2)
            elif len(pers_events) >= 2:
                target_indices = random.sample(pers_events, 2)
            
            if target_indices:
                idx1, idx2 = target_indices
                events[idx2]["time"] = events[idx1]["time"]
                events[idx1]["flexible"] = False
                events[idx2]["flexible"] = False
                events[idx1]["priority"] = "high"
                events[idx2]["priority"] = "high"
                has_conflict = True

    # Secondary Scan for natural conflicts (only same date)
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            if events[i]["date"] != events[j]["date"]: continue
            s1 = get_minutes(events[i]["time"])
            e1_end = s1 + events[i].get("duration", 60)
            s2 = get_minutes(events[j]["time"])
            e2_end = s2 + events[j].get("duration", 60)
            if s1 < e2_end and s2 < e1_end:
                has_conflict = True
                break
        if has_conflict: break

    return events, has_conflict

class AMALSEnvironment:
    def __init__(self):
        self.calendar = CalendarServer()
        self.step_count = 0
        self.max_steps = 3
        self.start_date = datetime(2026, 4, 26)
        self.reset()

    def reset(self):
        self.current_state = generate_schedule_conflict()
        self.current_state.current_date = self.start_date.strftime("%Y-%m-%d")
        self.events, self.has_conflict = generate_all_events(self.start_date)
        
        prof = [e for e in self.events if e["domain"] == "professional"]
        pers = [e for e in self.events if e["domain"] == "personal"]
        self.current_state.meeting_priority = prof[0]["priority"] if prof else "high"
        self.current_state.dinner_priority = pers[0]["priority"] if pers else "medium"
        self.current_state.dinner_flexible = pers[0]["flexible"] if pers else True
        
        self.calendar = CalendarServer()
        self.step_count = 0
        self.last_decision = None
        self.outcome = "pending"
        return self.get_observation()

    def get_observation(self):
        if not self.current_state: return {}
        obs = {
            "step": self.step_count,
            "current_date": self.current_state.current_date,
            "stress": round(self.current_state.stress, 2),
            "travel_time": self.current_state.travel_time,
            "events": self.events,
            "has_conflict": self.has_conflict 
        }
        if self.step_count == 0: obs["last_decision"], obs["outcome"] = None, None
        elif self.step_count == 1: obs["last_decision"], obs["outcome"] = self.last_decision, None
        else: obs["last_decision"], obs["outcome"] = self.last_decision, self.outcome
        return obs

    def state(self):
        return {"internal_truth": self.current_state, "events": self.events, "has_conflict": self.has_conflict, "step": self.step_count, "last_decision": self.last_decision, "outcome": self.outcome}

    def step(self, action):
        decision = action.get("decision")
        reward = 0
        
        # New: Action Costs
        costs = {
            "reschedule": -0.1, 
            "send_email": -0.05, 
            "skip_event": -0.4, 
            "delay_meeting": -0.2, 
            "partial_attend": -0.15,
            "move_to_next_day": -0.25
        }
        reward += costs.get(decision, 0)
        secondary = action.get("secondary_action")
        reward += costs.get(secondary, 0)

        if self.step_count == 0:
            self.last_decision = decision
            if decision == "move_to_next_day":
                reward += 0.1 # strategic move bonus
            reward += 0.2
        elif self.step_count == 1:
            # Execution phase
            success_prob = 0.7
            if self.current_state.stress > 0.6: success_prob -= 0.2
            success_prob = max(0.2, min(success_prob, 0.9))
            rand = random.random()
            if rand < success_prob: self.outcome = "success"; reward += 0.5
            elif rand < success_prob + 0.2: self.outcome = "partial"; reward += 0.2
            else: self.outcome = "failure"; reward -= 0.4
        elif self.step_count == 2:
            # Recovery
            if self.outcome == "failure":
                if decision in ["reschedule", "delay_meeting", "send_apology_email"]: reward += 0.5
                else: reward -= 0.3
            elif self.outcome == "success":
                reward += 0.1 # correct behavior bonus

        self.step_count += 1
        done = self.step_count >= self.max_steps
        return self.get_observation(), round(reward, 2), done, {"step": self.step_count, "outcome": self.outcome}
