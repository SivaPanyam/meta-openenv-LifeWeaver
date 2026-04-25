import random
from .scenarios import generate_schedule_conflict
from .reward import calculate_reward
from mcp_local.calendar_server import CalendarServer

class AMALSEnvironment:
    def __init__(self):
        self.calendar = CalendarServer()
        self.step_count = 0
        self.max_steps = 3
        self.current_state = None
        self.reset()

    def reset(self):
        """Resets the environment and returns the initial observation."""
        self.current_state = generate_schedule_conflict()
        self.calendar = CalendarServer()
        self.step_count = 0
        self.last_decision = None
        self.outcome = None
        return self.get_observation()

    def get_observation(self):
        """
        Returns a dictionary with ONLY visible information for the current step.
        Implements visibility rules to prevent information leakage.
        """
        if not self.current_state:
            return {}
            
        obs = {
            "step": self.step_count,
            "stress": round(self.current_state.stress, 2),
            "travel_time": self.current_state.travel_time,
            "meeting_priority": self.current_state.meeting_priority,
            "dinner_priority": self.current_state.dinner_priority
        }
        
        # Step-Based Visibility Rules
        if self.step_count == 0:
            obs["last_decision"] = None
            obs["outcome"] = None
        elif self.step_count == 1:
            obs["last_decision"] = self.last_decision
            obs["outcome"] = None
        else: # step >= 2
            obs["last_decision"] = self.last_decision
            obs["outcome"] = self.outcome
            
        return obs

    def state(self):
        """Returns the full internal state for debugging purposes only."""
        return {
            "internal_truth": self.current_state,
            "step": self.step_count,
            "last_decision": self.last_decision,
            "outcome": self.outcome
        }

    def step(self, action):
        """
        Executes one step in a 3-phase episode.
        Returns the next observation, reward, done flag, and info.
        """
        decision = action.get("decision")
        reward = 0
        recovery_actions = ["reschedule_meeting", "delay_dinner", "send_apology_email"]
        recovery_used = decision in recovery_actions
        
        info = {
            "step": self.step_count,
            "decision": decision,
            "outcome": self.outcome,
            "recovery_used": recovery_used
        }

        # --- PHASE 0: PLANNING ---
        if self.step_count == 0:
            info["phase"] = "planning"
            self.last_decision = decision
            reward = 0.2
            
            if decision == "attend_meeting":
                self.calendar.schedule_event("meeting", "8PM")
            elif decision == "attend_dinner":
                self.calendar.schedule_event("dinner", "8PM")
            elif decision == "balance_both":
                self.calendar.schedule_event("meeting", "8PM")
                self.calendar.schedule_event("dinner", "9PM")

        # --- PHASE 1: EXECUTION (Uncertainty Fix) ---
        elif self.step_count == 1:
            info["phase"] = "execution"
            
            success_prob = 0.7  # slightly lower base
            if self.current_state.stress > 0.6:
                success_prob -= 0.2
            if self.current_state.travel_time > 30:
                success_prob -= 0.2
            
            success_prob = max(0.2, min(success_prob, 0.9))
            rand = random.random()
            
            if rand < success_prob:
                self.outcome = "success"
                reward = 0.5
            elif rand < success_prob + 0.2:
                self.outcome = "partial"
                reward = 0.2
            else:
                self.outcome = "failure"
                reward = -0.4
            
            self.outcome = self.outcome
            info["outcome"] = self.outcome

        # --- PHASE 2: RECOVERY ---
        elif self.step_count == 2:
            info["phase"] = "recovery"
            
            if self.outcome == "failure":
                if recovery_used:
                    reward += 0.5   # Correct recovery
                else:
                    reward -= 0.3   # Missed recovery
            elif self.outcome == "success":
                if recovery_used:
                    reward -= 0.2   # Unnecessary recovery
                else:
                    reward += 0.1   # Correct behavior
            elif self.outcome == "partial":
                if recovery_used:
                    reward += 0.2   # Mild improvement

        # Increment step count
        self.step_count += 1
        done = self.step_count >= self.max_steps

        # Final Bonus (At last step)
        if done:
            if self.last_decision == "balance_both" and self.outcome != "failure":
                reward += 0.5

        return self.get_observation(), reward, done, info
