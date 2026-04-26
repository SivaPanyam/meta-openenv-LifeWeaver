import copy
from datetime import datetime, timedelta

def parse_event_times(event):
    """Helper to get start and end datetime objects for an event."""
    start_dt = datetime.strptime(f"{event['date']} {event['time']}", "%Y-%m-%d %H:%M")
    end_dt = start_dt + timedelta(minutes=event.get("duration", 60))
    return start_dt, end_dt

def format_event_time(dt):
    """Helper to convert datetime to HH:MM."""
    return dt.strftime("%H:%M")

def find_available_slot(events, duration, date_str, domain, buffer=15):
    """
    Finds the first available gap in the schedule for a specific date and domain.
    The buffer (travel_time) is respected between all events.
    Uses datetime for precision and handles cross-day limits.
    """
    # 1. Define Domain Windows (relative to start of requested date)
    base_date = datetime.strptime(date_str, "%Y-%m-%d")
    
    if domain == "professional":
        # 09:00 - 17:00
        windows = [(base_date.replace(hour=9, minute=0), base_date.replace(hour=17, minute=0))]
    else:
        # 06:00-08:00, 18:00-21:00
        windows = [
            (base_date.replace(hour=6, minute=0), base_date.replace(hour=8, minute=0)),
            (base_date.replace(hour=18, minute=0), base_date.replace(hour=21, minute=0))
        ]

    # 2. Get all events that might conflict (on requested date, or overlapping into it)
    relevant_events = []
    for e in events:
        start, end = parse_event_times(e)
        # Check if event exists on this date or overlaps into it
        if start.date() == base_date.date() or end.date() == base_date.date():
            relevant_events.append((start, end))
    
    relevant_events.sort()

    # 3. Search within allowed windows
    for win_start, win_end in windows:
        current_ptr = win_start
        
        for event_start, event_end in relevant_events:
            if event_end <= win_start: continue
            if event_start >= win_end: break
            
            # Check gap
            if (event_start - current_ptr).total_seconds() / 60 >= (duration + buffer):
                return format_event_time(current_ptr)
            
            current_ptr = max(current_ptr, event_end + timedelta(minutes=buffer))
            
        # Check remaining space
        if (win_end - current_ptr).total_seconds() / 60 >= duration:
            return format_event_time(current_ptr)

    return None

def move_to_next_day(state, event_type, buffer=15, max_lookahead=7, max_daily_events=6):
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

    for i in range(1, max_lookahead + 1):
        candidate_date = current_date_obj + timedelta(days=i)
        candidate_str = candidate_date.strftime("%Y-%m-%d")
        
        daily_count = len([e for e in events if e.get("date") == candidate_str])
        if daily_count >= max_daily_events:
            continue
            
        slot = find_available_slot(events, target_event.get("duration", 60), candidate_str, target_event.get("domain", "personal"), buffer=buffer)
        
        if slot:
            found_day = candidate_str
            final_time = slot
            break

    if not found_day:
        return state, {"status": "no_available_days_found"}

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
    t_start, t_end = parse_event_times(target)
    
    max_overlap = 0
    
    for i, other in enumerate(events):
        if i == target_idx: continue
            
        o_start, o_end = parse_event_times(other)
        
        overlap_start = max(t_start, o_start)
        overlap_end = min(t_end, o_end)
        
        if overlap_start < overlap_end:
            overlap = (overlap_end - overlap_start).total_seconds() / 60
            max_overlap = max(max_overlap, int(overlap))

    if max_overlap > 0:
        new_duration = max(15, target.get("duration", 60) - max_overlap)
        events[target_idx]["duration"] = new_duration
        events[target_idx]["type"] += " (Partial)"
        events[target_idx]["status"] = "partial_attendance"
        return new_state, {"status": "success", "resolved_overlap": max_overlap, "new_duration": new_duration}
        
    return state, {"status": "no_overlap_found"}

def detect_conflicts(state):
    """
    Scans the state for duration-based overlaps using datetime precision.
    Handles cross-day overlaps correctly.
    """
    events = state.get("events", [])
    conflicts = []
    
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            e1, e2 = events[i], events[j]
            
            s1, end1 = parse_event_times(e1)
            s2, end2 = parse_event_times(e2)
            
            if s1 < end2 and s2 < end1:
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
            # Logic for cross-day end_time
            _, end_dt = parse_event_times(event)
            original_date = datetime.strptime(event["date"], "%Y-%m-%d")
            if end_dt.date() > original_date.date():
                # Note: Currently we keep the start date, but mark as cross-day
                event["status"] += "_cross_day"
            found = True
            break
            
    return new_state, {"status": "success" if found else "event_not_found", "event": event_type, "new_time": new_time}
