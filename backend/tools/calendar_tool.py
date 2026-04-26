import copy
from datetime import datetime, timedelta

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

def find_available_slot(events, duration, date_str, buffer=15):
    """
    Finds the first available gap in the schedule for a specific date.
    """
    # Filter events by date
    daily_events = [e for e in events if e.get("date") == date_str]
    
    if not daily_events:
        return "09:00" # Default start for empty schedule

    # 1. Prepare and sort events
    time_slots = []
    for e in daily_events:
        start = get_minutes(e["time"])
        end = start + e.get("duration", 60)
        time_slots.append((start, end))
    
    time_slots.sort()

    # 2. Check gaps (start from 08:00 AM)
    current_time = 480 
    
    for start, end in time_slots:
        if start - current_time >= (duration + buffer):
            return format_minutes(current_time)
        current_time = max(current_time, end + buffer)

    return format_minutes(current_time)

def move_to_next_day(state, event_type):
    """
    Moves an event to the next day and finds an available slot.
    """
    new_state = copy.deepcopy(state)
    events = new_state.get("events", [])
    
    target_event = None
    for event in events:
        if event["type"] == event_type:
            target_event = event
            break
    
    if not target_event:
        return state, {"status": "event_not_found"}

    # 1. Calculate new date
    current_date = datetime.strptime(target_event["date"], "%Y-%m-%d")
    next_day = current_date + timedelta(days=1)
    next_day_str = next_day.strftime("%Y-%m-%d")

    # 2. Find slot on next day
    new_time = find_available_slot(events, target_event.get("duration", 60), next_day_str)
    
    # 3. Update event
    target_event["date"] = next_day_str
    target_event["time"] = new_time
    target_event["status"] = "moved_to_next_day"
    
    return new_state, {
        "status": "success", 
        "event": event_type, 
        "original_date": current_date.strftime("%Y-%m-%d"),
        "new_date": next_day_str,
        "new_time": new_time
    }

def detect_conflicts(state):
    """
    Scans the state for duration-based overlaps on the same date.
    """
    events = state.get("events", [])
    conflicts = []
    
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            e1, e2 = events[i], events[j]
            if e1.get("date") != e2.get("date"): continue
            
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
    """
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
