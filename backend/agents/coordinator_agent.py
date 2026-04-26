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

def get_state_summary(events):
    prof = any(e for e in events if e["domain"] == "professional")
    pers = any(e for e in events if e["domain"] == "personal")
    
    if prof and pers: return "double_high_conflict"
    return "standard_conflict"

def coordinator_agent(state, agent_outputs):
    """
    Hybrid coordinator combining:
    1. ML Prediction (RandomForest)
    2. Historical Memory (Case-based)
    3. Heuristic Rules (Fallback)
    """
    events = state.get("events", [])
    reasoning = [o["reason"] for o in agent_outputs if "reason" in o]
    
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
    summary = get_state_summary(events)
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
