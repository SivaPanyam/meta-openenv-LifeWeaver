import copy

def get_minutes(time_str):
    """Helper to convert HH:MM to absolute minutes."""
    try:
        h, m = map(int, time_str.split(":"))
        return h * 60 + m
    except:
        return 0

def format_minutes(minutes):
    """Helper to convert absolute minutes to HH:MM."""
    h = (minutes // 60) % 24
    m = minutes % 60
    return f"{h:02d}:{m:02d}"

def find_available_slot(events, duration, buffer=15):
    """
    Finds the first available gap in the schedule.
    Logic:
    - Sort events by time
    - Check gaps between events
    - If no gap found, return 30 mins after the last event
    """
    if not events:
        return "09:00" # Default start for empty schedule

    # 1. Prepare and sort events
    time_slots = []
    for e in events:
        start = get_minutes(e["time"])
        end = start + e.get("duration", 60)
        time_slots.append((start, end))
    
    time_slots.sort()

    # 2. Check gaps
    # Start checking from the earliest reasonable time (e.g., 08:00)
    current_time = 480 # 08:00 AM
    
    for start, end in time_slots:
        if start - current_time >= (duration + buffer):
            return format_minutes(current_time)
        current_time = max(current_time, end + buffer)

    # 3. No gap found, append after last event
    return format_minutes(current_time)

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
