import sys
import os

try:
    from memory_store import get_best_action_from_memory
    from ml_logic import get_ml_features, predict_ml_action
    from tools.calendar_tool import detect_conflicts
except ImportError:
    try:
        from agents.memory_store import get_best_action_from_memory
        from agents.ml_logic import get_ml_features, predict_ml_action
        from tools.calendar_tool import detect_conflicts
    except ImportError:
        # Final fallback for evaluation script context
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory"))
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from memory_store import get_best_action_from_memory
        from ml_logic import get_ml_features, predict_ml_action
        from calendar_tool import detect_conflicts

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

    # 2. Strategy: Exhaustively resolve conflicts
    processed_events = set()
    
    # We loop through the pairs of conflicts directly
    for e1_name, e2_name in conflicts:
        # If this specific collision is already resolved (one or both events moved)
        if e1_name in processed_events and e2_name in processed_events: continue
        
        e1 = next(e for e in events if e["type"] == e1_name)
        e2 = next(e for e in events if e["type"] == e2_name)

        # Selection: Which event to move?
        # If one is already processed, we MUST move the other one to solve the remaining overlap
        if e1_name in processed_events:
            target_event = e2
        elif e2_name in processed_events:
            target_event = e1
        else:
            # Both new: Move the more flexible/lower priority one
            target_event = e2 if (e1.get("priority") == "high" or not e1.get("flexible")) else e1

        target_name = target_event["type"]

        # A. Rigid Deadlock Check (only if both are high-prio/rigid)
        # If we are forced to move a rigid one because the other is already processed, we escalate
        other_name = e2_name if target_name == e1_name else e1_name
        other_event = e2 if target_name == e1_name else e1
        
        if target_event.get("priority") == "high" and not target_event.get("flexible") and \
           other_event.get("priority") == "high" and not other_event.get("flexible"):
            final_actions.append({
                "action": "escalate_conflict", 
                "target": f"{e1_name} & {e2_name}", 
                "description": "Rigid high-priority deadlock."
            })
            processed_events.update([e1_name, e2_name])
            continue

        # B. Resolve via Move or Reschedule
        if stress > 0.7 or len([e for e in events if e.get("date") == today]) > 4:
            if target_event.get("flexible") or target_event.get("priority") == "low":
                final_actions.append({
                    "action": "move_to_next_day", 
                    "target": target_name, 
                    "description": "Multi-day move for balance."
                })
                processed_events.add(target_name)
                continue

        # C. Fallback: Reschedule or ML
        features = get_ml_features({"events": [target_event], "has_conflict": True, "stress": stress})
        ml_action, confidence = predict_ml_action(features)
        action = ml_action if (ml_action and confidence > 0.7) else "reschedule"

        final_actions.append({
            "action": action,
            "target": target_name,
            "description": f"Resolving overlap via {action}."
        })
        processed_events.add(target_name)

    # 3. DEADLOCK FALLBACK: Ensure every conflict has a plan
    if not final_actions:
        return {"final_action": {"action": "no_change"}, "reasoning": reasoning}

    return {
        "final_actions": final_actions,
        "reasoning": reasoning
    }
