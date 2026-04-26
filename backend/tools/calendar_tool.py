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

def find_available_slot(events, duration, date_str, domain, buffer=15):
    """
    Finds the first available gap in the schedule for a specific date and domain.
    """
    # 1. Define Domain Windows (in minutes)
    if domain == "professional":
        windows = [(540, 1020)] # 09:00 - 17:00
    else:
        windows = [(360, 480), (1080, 1260)] # 06:00-08:00, 18:00-21:00

    # 2. Filter events by date
    daily_events = [e for e in events if e.get("date") == date_str]
    time_slots = []
    for e in daily_events:
        start = get_minutes(e["time"])
        end = start + e.get("duration", 60)
        time_slots.append((start, end))
    time_slots.sort()

    # 3. Search within allowed windows
    for win_start, win_end in windows:
        current_ptr = win_start
        
        # Check gaps between events that fall within this window
        for event_start, event_end in time_slots:
            # Skip events that end before window starts
            if event_end <= win_start: continue
            # Stop if event starts after window ends
            if event_start >= win_end: break
            
            # Check gap between current_ptr and next event
            if event_start - current_ptr >= (duration + buffer):
                return format_minutes(current_ptr)
            
            current_ptr = max(current_ptr, event_end + buffer)
            
        # Check remaining space in window after last event
        if win_end - current_ptr >= duration:
            return format_minutes(current_ptr)

    return None

def move_to_next_day(state, event_type, max_lookahead=7, max_daily_events=6):
    """
    Moves an event to the FIRST available day that isn't overcrowded.
    """
    new_state = copy.deepcopy(state)
    events = new_state.get("events", [])
    
    target_event = next((e for e in events if e["type"] == event_type), None)
    if not target_event:
        return state, {"status": "event_not_found"}

    current_date_obj = datetime.strptime(target_event["date"], "%Y-%m-%d")
    found_day = None
    final_time = None

    # Search for the first viable day within the next 7 days
    for i in range(1, max_lookahead + 1):
        candidate_date = current_date_obj + timedelta(days=i)
        candidate_str = candidate_date.strftime("%Y-%m-%d")
        
        # 1. Check density
        daily_count = len([e for e in events if e.get("date") == candidate_str])
        if daily_count >= max_daily_events:
            continue
            
        # 2. Check for slot (WITH DOMAIN)
        slot = find_available_slot(events, target_event.get("duration", 60), candidate_str, target_event.get("domain", "personal"))
        
        if slot:
            found_day = candidate_str
            final_time = slot
            break

    if not found_day:
        return state, {"status": "no_available_days_found", "message": f"Could not find a slot within {max_lookahead} days."}

    # Update event
    original_date = target_event["date"]
    target_event["date"] = found_day
    target_event["time"] = final_time
    target_event["status"] = "moved_to_future_day"
    
    return new_state, {
        "status": "success", 
        "event": event_type, 
        "original_date": original_date,
        "new_date": found_day,
        "new_time": final_time,
        "days_shifted": (datetime.strptime(found_day, "%Y-%m-%d") - datetime.strptime(original_date, "%Y-%m-%d")).days
    }

def apply_partial_attendance(state, event_type):
    """
    Reduces duration of an event by the exact overlap amount to resolve conflict.
    """
    new_state = copy.deepcopy(state)
    events = new_state.get("events", [])
    
    target_idx = next((i for i, e in enumerate(events) if e["type"] == event_type), None)
    if target_idx is None:
        return state, {"status": "event_not_found"}

    target = events[target_idx]
    t_start = get_minutes(target["time"])
    t_end = t_start + target.get("duration", 60)
    
    max_overlap = 0
    
    # Find the largest overlap with any other event on the same day
    for i, other in enumerate(events):
        if i == target_idx or other.get("date") != target.get("date"):
            continue
            
        o_start = get_minutes(other["time"])
        o_end = o_start + other.get("duration", 60)
        
        # Calculate overlap
        overlap_start = max(t_start, o_start)
        overlap_end = min(t_end, o_end)
        
        if overlap_start < overlap_end:
            overlap = overlap_end - overlap_start
            max_overlap = max(max_overlap, overlap)

    if max_overlap > 0:
        new_duration = max(15, target.get("duration", 60) - max_overlap)
        events[target_idx]["duration"] = new_duration
        events[target_idx]["type"] += " (Partial)"
        events[target_idx]["status"] = "partial_attendance"
        return new_state, {"status": "success", "resolved_overlap": max_overlap, "new_duration": new_duration}
        
    return state, {"status": "no_overlap_found"}

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
