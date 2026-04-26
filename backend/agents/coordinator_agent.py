import sys
import os

# Robust path handling for memory
try:
    from memory_store import get_best_action_from_memory
except ImportError:
    try:
        from agents.memory_store import get_best_action_from_memory
    except ImportError:
        # Final fallback for evaluation script context
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory"))
        from memory_store import get_best_action_from_memory

def get_state_summary(events):
    prof = any(e for e in events if e["domain"] == "professional")
    pers = any(e for e in events if e["domain"] == "personal")
    
    if prof and pers: return "double_high_conflict"
    return "standard_conflict"

def coordinator_agent(state, agent_outputs):
    """
    Enhanced coordinator supporting multiple strategies:
    - reschedule
    - delay_meeting
    - partial_attend
    - skip_event
    """
    events = state.get("events", [])
    reasoning = [o["reason"] for o in agent_outputs if "reason" in o]
    
    summary = get_state_summary(events)
    best_past_action = get_best_action_from_memory(summary)
    
    prof_event = next((e for e in events if e["domain"] == "professional"), None)
    pers_event = next((e for e in events if e["domain"] == "personal"), None)
    
    # 1. Memory Override
    if best_past_action and best_past_action != "no_change":
        memory_reason = f"Memory Insight: Historically, '{best_past_action}' was the optimal trade-off for this complex state."
        reasoning.append(memory_reason)
        return {
            "final_action": {
                "action": best_past_action, 
                "target": events[0]["type"], 
                "description": f"Applied memory-optimized strategy: {best_past_action}. {memory_reason}"
            },
            "reasoning": reasoning
        }

    # 2. Strategy Branching (Logic)
    if summary == "complex_high_conflict":
        # Strategy: Partial Attendance (Compromise)
        return {
            "final_action": {"action": "partial_attend", "target": prof_event["type"] if prof_event else "task", "description": "Complex overlap between non-flexible high-priority tasks. Choosing partial attendance for both."},
            "reasoning": reasoning
        }
    
    elif prof_event and not prof_event.get("flexible"):
        # Strategy: Delay or Reschedule the other
        target = pers_event["type"] if pers_event else "task"
        return {
            "final_action": {"action": "reschedule", "target": target, "description": f"Professional task is rigid. Shifting personal task '{target}'."},
            "reasoning": reasoning
        }

    return {
        "final_action": {"action": "reschedule", "target": events[0]["type"], "description": "Standard conflict resolution via rescheduling."},
        "reasoning": reasoning
    }
