def get_time_range(event):
    """Converts event time and duration into absolute minutes from start of day."""
    try:
        h, m = map(int, event["time"].split(":"))
        start = h * 60 + m
        end = start + event.get("duration", 60)
        return start, end
    except:
        return 0, 0

def calendar_agent(state):
    """
    Detects realistic time conflicts based on duration overlap.
    Condition: start1 < end2 AND start2 < end1
    """
    events = state.get("events", [])
    prio_map = {"high": 3, "medium": 2, "low": 1}
    
    conflicts = []
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            s1, e1 = get_time_range(events[i])
            s2, e2 = get_time_range(events[j])
            
            if s1 < e2 and s2 < e1:
                conflicts.append((events[i], events[j]))
    
    if not conflicts:
        return {
            "agent": "calendar_agent",
            "action": "no_conflict",
            "reason": "No overlapping events detected in the schedule."
        }
    
    # Resolve first conflict by choosing lowest priority event
    e1, e2 = conflicts[0]
    target = e1 if prio_map.get(e1["priority"], 0) <= prio_map.get(e2["priority"], 0) else e2
    
    return {
        "agent": "calendar_agent",
        "action": "reschedule",
        "target_event": target["type"],
        "reason": f"Detected overlap between '{e1['type']}' and '{e2['type']}'. Suggesting rescheduling '{target['type']}' due to lower relative priority."
    }
