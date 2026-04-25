def calendar_agent(state):
    """
    Detects time conflicts and suggests rescheduling for the lowest priority event.
    """
    events = state.get("events", [])
    prio_map = {"high": 3, "medium": 2, "low": 1}
    
    # Group events by time
    time_map = {}
    for event in events:
        t = event["time"]
        if t not in time_map:
            time_map[t] = []
        time_map[t].append(event)
    
    # Detect conflicts
    conflicts = [group for group in time_map.values() if len(group) > 1]
    
    if not conflicts:
        return {
            "agent": "calendar_agent",
            "action": "no_conflict",
            "reason": "No overlapping events detected in the schedule."
        }
    
    # Identify the lowest priority event in the first conflict found
    first_conflict = conflicts[0]
    target = min(first_conflict, key=lambda x: prio_map.get(x["priority"], 0))
    
    return {
        "agent": "calendar_agent",
        "action": "reschedule",
        "target_event": target["type"],
        "reason": f"Detected overlap at {target['time']}. Suggesting rescheduling '{target['type']}' due to lower relative priority ({target['priority']})."
    }
