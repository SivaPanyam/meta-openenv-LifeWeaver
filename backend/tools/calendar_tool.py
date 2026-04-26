import copy

def get_minutes(time_str):
    """Helper to convert HH:MM to absolute minutes."""
    try:
        h, m = map(int, time_str.split(":"))
        return h * 60 + m
    except:
        return 0

def detect_conflicts(state):
    """
    Scans the state for duration-based overlaps.
    Returns a list of conflicting event pairs.
    """
    events = state.get("events", [])
    conflicts = []
    
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            e1, e2 = events[i], events[j]
            
            s1 = get_minutes(e1["time"])
            e1_end = s1 + e1.get("duration", 60)
            
            s2 = get_minutes(e2["time"])
            e2_end = s2 + e2.get("duration", 60)
            
            if s1 < e2_end and s2 < e1_end:
                conflicts.append((e1["type"], e2["type"]))
                
    return conflicts

def reschedule_event(state, event_type, new_time):
    """
    Finds an event by type and updates its start time.
    Returns a new copy of the state with the modification.
    """
    print(f"Rescheduling {event_type} to {new_time}")
    new_state = copy.deepcopy(state)
    events = new_state.get("events", [])
    
    found = False
    for event in events:
        if event["type"] == event_type:
            event["time"] = new_time
            event["status"] = "rescheduled"
            found = True
            break
            
    return new_state, {"status": "success" if found else "event_not_found", "event": event_type, "new_time": new_time}
