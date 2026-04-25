import random
import copy
from .scenarios import generate_schedule_conflict
from .reward import calculate_reward
from mcp_local.calendar_server import CalendarServer

# --- PART 1: Source-Specific Generators ---

def generate_email_events():
    """Generates structured, work-related events from email."""
    pool = [
        {"type": "team_meeting", "priority": "high", "flexible": False},
        {"type": "client_call", "priority": "high", "flexible": False},
        {"type": "project_sync", "priority": "medium", "flexible": False},
        {"type": "urgent_fix", "priority": "high", "flexible": False}
    ]
    # Copy to avoid pool mutation
    selected = [copy.deepcopy(e) for e in random.sample(pool, k=random.randint(1, 2))]
    for e in selected: e["source"] = "email"
    return selected

def generate_conversation_events():
    """Generates informal, social/family events from conversations."""
    pool = [
        {"type": "family_dinner", "priority": "high", "flexible": True},
        {"type": "friend_hangout", "priority": "medium", "flexible": True},
        {"type": "quick_chat", "priority": "low", "flexible": True},
        {"type": "birthday_planning", "priority": "medium", "flexible": True}
    ]
    selected = [copy.deepcopy(e) for e in random.sample(pool, k=random.randint(1, 2))]
    for e in selected: e["source"] = "conversation"
    return selected

def generate_calendar_events():
    """Generates existing commitments from the calendar."""
    pool = [
        {"type": "deep_work", "priority": "high", "flexible": True},
        {"type": "learning", "priority": "medium", "flexible": True},
        {"type": "dentist_appt", "priority": "medium", "flexible": False},
        {"type": "workshop", "priority": "medium", "flexible": False}
    ]
    selected = [copy.deepcopy(e) for e in random.sample(pool, k=random.randint(1, 2))]
    for e in selected: e["source"] = "calendar"
    return selected

def generate_manual_events():
    """Generates personal tasks added manually by the user."""
    pool = [
        {"type": "gym", "priority": "medium", "flexible": True},
        {"type": "grocery_run", "priority": "low", "flexible": True},
        {"type": "laundry", "priority": "low", "flexible": True}
    ]
    selected = [copy.deepcopy(e) for e in random.sample(pool, k=random.randint(0, 1))]
    for e in selected: e["source"] = "manual"
    return selected

# --- PART 2 & 3: Time Assignment and Merging ---

def assign_time_and_duration(events):
    """Assigns random times between 6 PM - 10 PM and durations."""
    for event in events:
        hour = random.randint(18, 21) # 6 PM to 9 PM start
        event["time"] = f"{hour}:00 PM"
        event["duration"] = random.choice([30, 60, 90])
    return events

def generate_all_events():
    """Merges all sources into one unified, realistic list."""
    events = []
    events += generate_email_events()
    events += generate_conversation_events()
    events += generate_calendar_events()
    events += generate_manual_events()
    
    # Randomize order so sources are mixed
    random.shuffle(events)
    
    # Assign physical constraints
    assign_time_and_duration(events)
    return events

# --- AMALS Environment ---

class AMALSEnvironment:
    def __init__(self):
        self.calendar = CalendarServer()
        self.step_count = 0
        self.max_steps = 3
        self.current_state = None
        self.events = []
        self.reset()

    def reset(self):
        """Resets the environment with multi-source events."""
        self.current_state = generate_schedule_conflict()
        
        # PART 4: Update reset with multi-source logic
        self.events = generate_all_events()
        
        # Legacy compatibility mapping for reward/training consistency
        # We find a work-like event and a social-like event for the core conflict logic
        work_events = [e for e in self.events if e["source"] == "email" or e["priority"] == "high"]
        social_events = [e for e in self.events if e["source"] == "conversation" or e["flexible"]]
        
        self.current_state.meeting_priority = work_events[0]["priority"] if work_events else "medium"
        self.current_state.dinner_priority = social_events[0]["priority"] if social_events else "medium"
        self.current_state.dinner_flexible = social_events[0]["flexible"] if social_events else True
        
        self.calendar = CalendarServer()
        self.step_count = 0
        self.last_decision = None
        self.outcome = None
        return self.get_observation()

    def get_observation(self):
        """Returns a dictionary with visible information."""
        if not self.current_state:
            return {}
            
        obs = {
            "step": self.step_count,
            "stress": round(self.current_state.stress, 2),
            "travel_time": self.current_state.travel_time,
            "meeting_priority": self.current_state.meeting_priority,
            "dinner_priority": self.current_state.dinner_priority,
            "dinner_flexible": self.current_state.dinner_flexible,
            "events": self.events # Full multi-source list
        }
        
        if self.step_count == 0:
            obs["last_decision"], obs["outcome"] = None, None
        elif self.step_count == 1:
            obs["last_decision"], obs["outcome"] = self.last_decision, None
        else:
            obs["last_decision"], obs["outcome"] = self.last_decision, self.outcome
            
        return obs

    def state(self):
        """Returns the full internal state."""
        return {
            "internal_truth": self.current_state,
            "events": self.events,
            "step": self.step_count,
            "last_decision": self.last_decision,
            "outcome": self.outcome
        }

    def step(self, action):
        """Executes one step in the 3-phase episode."""
        decision = action.get("decision")
        reward = 0
        recovery_actions = ["reschedule_meeting", "delay_dinner", "send_apology_email"]
        recovery_used = decision in recovery_actions
        
        info = {"step": self.step_count, "decision": decision, "outcome": self.outcome, "recovery_used": recovery_used}

        # --- PHASE 0: PLANNING ---
        if self.step_count == 0:
            info["phase"] = "planning"
            self.last_decision = decision
            reward = 0.2
            # Simulate tool usage for the primary conflict
            if decision == "attend_meeting":
                self.calendar.schedule_event("primary_work_task", "8:00 PM")
            elif decision == "attend_dinner":
                self.calendar.schedule_event("primary_social_task", "8:00 PM")
            elif decision == "balance_both":
                self.calendar.schedule_event("primary_work_task", "8:00 PM")
                self.calendar.schedule_event("primary_social_task", "9:00 PM")

        # --- PHASE 1: EXECUTION ---
        elif self.step_count == 1:
            info["phase"] = "execution"
            success_prob = 0.7
            if self.current_state.stress > 0.6: success_prob -= 0.2
            if self.current_state.travel_time > 30: success_prob -= 0.2
            success_prob = max(0.2, min(success_prob, 0.9))
            
            rand = random.random()
            if rand < success_prob: self.outcome = "success"; reward = 0.5
            elif rand < success_prob + 0.2: self.outcome = "partial"; reward = 0.2
            else: self.outcome = "failure"; reward = -0.4
            info["outcome"] = self.outcome

        # --- PHASE 2: RECOVERY ---
        elif self.step_count == 2:
            info["phase"] = "recovery"
            if self.outcome == "failure":
                reward += 0.5 if recovery_used else -0.3
            elif self.outcome == "success":
                reward += -0.2 if recovery_used else 0.1
            elif self.outcome == "partial":
                if recovery_used: reward += 0.2

        self.step_count += 1
        done = self.step_count >= self.max_steps
        if done and self.last_decision == "balance_both" and self.outcome != "failure":
            reward += 0.5

        return self.get_observation(), reward, done, info
