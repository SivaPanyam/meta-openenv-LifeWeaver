def social_agent(state):
    """
    Advocates for personal and social commitments during scheduling conflicts.
    """
    events = state.get("events", [])
    
    # Detect personal events in conflict
    pers_event = next((e for e in events if e.get("domain") == "personal"), None)
    
    if pers_event:
        return {
            "agent": "social_agent",
            "action": "protect_personal",
            "target_event": pers_event["type"],
            "reason": f"Personal commitment '{pers_event['type']}' is vital for work-life balance."
        }
    
    return {
        "agent": "social_agent",
        "action": "no_opinion",
        "reason": "No personal events detected to advocate for."
    }
