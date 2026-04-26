def career_agent(state):
    """
    Advocates for professional commitments during scheduling conflicts.
    """
    events = state.get("events", [])
    
    # Detect professional events in conflict
    # (Simplified: check if any professional event exists)
    prof_event = next((e for e in events if e.get("domain") == "professional"), None)
    
    if prof_event:
        return {
            "agent": "career_agent",
            "action": "protect_professional",
            "target_event": prof_event["type"],
            "reason": f"Professional commitment '{prof_event['type']}' is critical for career progression."
        }
    
    return {
        "agent": "career_agent",
        "action": "no_opinion",
        "reason": "No professional events detected to advocate for."
    }
