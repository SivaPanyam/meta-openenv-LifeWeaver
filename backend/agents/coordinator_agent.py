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
    Hybrid coordinator combining:
    1. Rigid Conflict Detection (Escalation)
    2. ML Prediction (RandomForest)
    3. Historical Memory (Case-based)
    4. Multi-day Strategy (move_to_next_day)
    5. Heuristic Rules (Fallback)
    """
    events = state.get("events", [])
    stress = state.get("stress", 0.0)
    reasoning = [o["reason"] for o in agent_outputs if "reason" in o]
    
    # --- LAYER 0: RIGID CONFLICT DETECTION ---
    # Check if there's a conflict where both are high-prio and non-flexible
    conflicts = []
    # Simplified conflict scan for coordination logic
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            e1, e2 = events[i], events[j]
            if e1.get("date") != e2.get("date"): continue
            
            s1 = get_ml_features({"events": [e1]}).get("prof_count", 0) # Dummy use of features
            # Re-implementing overlap check here for coordination context
            start1 = sum(x * int(t) for x, t in zip([60, 1], e1["time"].split(":")))
            end1 = start1 + e1.get("duration", 60)
            start2 = sum(x * int(t) for x, t in zip([60, 1], e2["time"].split(":")))
            end2 = start2 + e2.get("duration", 60)

            if start1 < end2 and start2 < end1:
                if e1.get("priority") == "high" and not e1.get("flexible") and \
                   e2.get("priority") == "high" and not e2.get("flexible"):
                    reason = f"Rigid conflict detected between '{e1['type']}' and '{e2['type']}'. Both are high priority and inflexible."
                    reasoning.append(reason)
                    return {
                        "final_action": {
                            "action": "escalate_conflict", 
                            "target": "user", 
                            "description": "User intervention required: Cannot automatically resolve overlapping high-priority rigid commitments."
                        },
                        "reasoning": reasoning
                    }

    # 0. Multi-day Strategy: Move to next day if stressed or schedule too dense
    today = state.get("current_date")
    today_events = [e for e in events if e.get("date") == today]
    
    if stress > 0.7 or len(today_events) > 4:
        # Pick a flexible or low-priority event to move
        movable = next((e for e in today_events if e.get("flexible") or e.get("priority") == "low"), None)
        if movable:
            reason = "High stress or dense schedule detected. Moving non-critical task to tomorrow for better balance."
            reasoning.append(reason)
            return {
                "final_action": {
                    "action": "move_to_next_day", 
                    "target": movable["type"], 
                    "description": reason
                },
                "reasoning": reasoning
            }

    # --- HYBRID LAYER 1: ML PREDICTION ---
    features = get_ml_features(state)
    ml_action, confidence = predict_ml_action(features)
    
    if ml_action and confidence > 0.6:
        reasoning.append(f"ML Insight: Classifier (conf={confidence:.2f}) recommends '{ml_action}'.")
        return {
            "final_action": {
                "action": ml_action, 
                "target": events[0]["type"] if events else "task", 
                "description": f"ML-driven decision ({ml_action}) based on current schedule features."
            },
            "reasoning": reasoning
        }

    # --- HYBRID LAYER 2: HISTORICAL MEMORY ---
    summary = get_state_summary(events, stress)
    best_past_action = get_best_action_from_memory(summary)
    
    if best_past_action and best_past_action != "no_change":
        memory_reason = f"Memory Insight: Historically, '{best_past_action}' was optimal for this state."
        reasoning.append(memory_reason)
        return {
            "final_action": {
                "action": best_past_action, 
                "target": events[0]["type"] if events else "task", 
                "description": f"Memory-optimized strategy: {best_past_action}."
            },
            "reasoning": reasoning
        }

    # --- HYBRID LAYER 3: HEURISTIC RULES (FALLBACK) ---
    prof_event = next((e for e in events if e["domain"] == "professional"), None)
    pers_event = next((e for e in events if e["domain"] == "personal"), None)
    
    if prof_event and not prof_event.get("flexible"):
        target = pers_event["type"] if pers_event else "task"
        return {
            "final_action": {"action": "reschedule", "target": target, "description": "Heuristic: Professional task is rigid. Rescheduling personal."},
            "reasoning": reasoning
        }

    return {
        "final_action": {"action": "reschedule", "target": events[0]["type"] if events else "task", "description": "Standard rule-based rescheduling."},
        "reasoning": reasoning
    }
