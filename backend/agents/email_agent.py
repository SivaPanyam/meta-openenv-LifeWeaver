def email_agent(state):
    """
    Suggests notification emails if scheduling conflicts are present.
    """
    events = state.get("events", [])
    
    # Check for any overlapping times
    times = [e["time"] for e in events]
    has_conflict = len(times) != len(set(times))
    
    if not has_conflict:
        return {
            "agent": "email_agent",
            "action": "no_action",
            "reason": "No conflicts detected; no notifications required."
        }
    
    return {
        "agent": "email_agent",
        "action": "send_email",
        "message": "Notify participants about potential delays due to schedule overlap.",
        "reason": "Conflicts detected in the calendar. Proactive communication recommended."
    }
