def get_minutes(time_str):
    try:
        h, m = map(int, time_str.split(":"))
        return h * 60 + m
    except:
        return 0

def find_conflicting_events(events):
    """Reuses overlap logic to identify specific conflicting pairs."""
    conflicts = []
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            e1, e2 = events[i], events[j]
            s1 = get_minutes(e1["time"])
            e1_end = s1 + e1.get("duration", 60)
            s2 = get_minutes(e2["time"])
            e2_end = s2 + e2.get("duration", 60)
            
            if s1 < e2_end and s2 < e1_end:
                conflicts.extend([e1["type"], e2["type"]])
    return list(set(conflicts))

def generate_explanation(old_state, agent_outputs, final_action, tools_used, new_state):
    """
    Constructs a structured explanation of the entire decision lifecycle.
    """
    old_events = old_state.get("events", [])
    new_events = new_state.get("events", [])
    
    conflict_list = find_conflicting_events(old_events)
    
    # Map agent outputs to a friendly dict
    opinions = {}
    for output in agent_outputs:
        name = output["agent"].replace("_agent", "")
        opinions[name] = output["reason"]

    return {
        "conflict_detected": len(conflict_list) > 0,
        "conflict_events": conflict_list,
        
        "agent_opinions": opinions,
        
        "final_decision": final_action,
        
        "action_taken": tools_used,
        
        "state_change": {
            "before": old_events,
            "after": new_events
        }
    }
