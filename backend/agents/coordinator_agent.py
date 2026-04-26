import sys
import os

try:
    from memory_store import get_best_action_from_memory
    from ml_logic import get_ml_features, predict_ml_action
except ImportError:
    try:
        from agents.memory_store import get_best_action_from_memory
        from agents.ml_logic import get_ml_features, predict_ml_action
    except ImportError:
        # Final fallback for evaluation script context
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory"))
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from memory_store import get_best_action_from_memory
        from ml_logic import get_ml_features, predict_ml_action

def get_state_summary(events, stress=0.0):
    prof = any(e for e in events if e["domain"] == "professional")
    pers = any(e for e in events if e["domain"] == "personal")
    
    if stress > 0.7: return "high_stress_state"
    if prof and pers: return "double_high_conflict"
    return "standard_conflict"

def coordinator_agent(state, agent_outputs):
    """
    Hybrid coordinator supporting Recursive Resolution (multiple actions).
    """
    events = state.get("events", [])
    stress = state.get("stress", 0.0)
    reasoning = [o["reason"] for o in agent_outputs if "reason" in o]
    today = state.get("current_date")
    
    final_actions = []

    # 1. Identify ALL conflicts
    conflicts = detect_conflicts(state)
    if not conflicts:
        return {"final_action": {"action": "no_change"}, "reasoning": reasoning}

    # 2. Strategy: Process conflicts one by one
    # To avoid ping-pong, we try to solve as many as possible in one turn
    processed_events = set()

    for e1_name, e2_name in conflicts:
        if e1_name in processed_events or e2_name in processed_events: continue
        
        e1 = next(e for e in events if e["type"] == e1_name)
        e2 = next(e for e in events if e["type"] == e2_name)

        # A. Rigid Deadlock (Layer 0)
        if e1.get("priority") == "high" and not e1.get("flexible") and \
           e2.get("priority") == "high" and not e2.get("flexible"):
            final_actions.append({
                "action": "escalate_conflict", 
                "target": f"{e1_name} & {e2_name}", 
                "description": "User intervention required: Multiple rigid high-priority commitments."
            })
            processed_events.update([e1_name, e2_name])
            continue

        # B. Multi-day Move (Layer 1)
        if stress > 0.7 or len([e for e in events if e.get("date") == today]) > 4:
            movable = e1 if (e1.get("flexible") or e1.get("priority") == "low") else e2 if (e2.get("flexible") or e2.get("priority") == "low") else None
            if movable:
                final_actions.append({
                    "action": "move_to_next_day", 
                    "target": movable["type"], 
                    "description": "Moving to future day due to stress/density."
                })
                processed_events.add(movable["type"])
                continue

        # C. Partial Attend or Reschedule (Layer 2)
        # Choose the more flexible/lower priority one to modify
        target = e2 if e1.get("priority") == "high" else e1
        
        # ML check for target
        features = get_ml_features({"events": [target], "has_conflict": True, "stress": stress})
        ml_action, confidence = predict_ml_action(features)
        
        action = ml_action if (ml_action and confidence > 0.6) else "reschedule"
        
        final_actions.append({
            "action": action,
            "target": target["type"],
            "description": f"Resolving overlap with {target['type']} via {action}."
        })
        processed_events.add(target["type"])

    return {
        "final_actions": final_actions,
        "reasoning": reasoning
    }
