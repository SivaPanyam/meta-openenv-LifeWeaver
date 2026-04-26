def get_time_range(event):
    """Converts event time and duration into absolute minutes from start of day."""
    try:
        h, m = map(int, event["time"].split(":"))
        start = h * 60 + m
        end = start + event.get("duration", 60)
        return start, end
    except:
        return 0, 0

def email_agent(state):
    """
    Suggests notification emails if scheduling conflicts (overlaps) are present.
    """
    events = state.get("events", [])
    
    has_overlap = False
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            s1, e1 = get_time_range(events[i])
            s2, e2 = get_time_range(events[j])
            
            if s1 < e2 and s2 < e1:
                has_overlap = True
                break
        if has_overlap: break
    
    if not has_overlap:
        return {
            "agent": "email_agent",
            "action": "no_action",
            "reason": "No schedule conflicts requiring notification."
        }
    
    return {
        "agent": "email_agent",
        "action": "send_email",
        "message": "Notify participants about delay due to conflict",
        "reason": "Duration-based overlaps detected. Proactive communication recommended."
    }
