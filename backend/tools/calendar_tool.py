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

def find_available_slot(events, duration, date_str, domain, buffer=15, crunch_mode=False):
    """
    Finds the first available gap in the schedule for a specific date and domain.
    - Cross-Day Buffer: Considers ALL events to prevent midnight 'leaks'.
    - Crunch Mode: Expands windows if no slot is found in standard hours.
    """
    base_date = datetime.strptime(date_str, "%Y-%m-%d")
    
    # 1. Define Windows (Standard vs Crunch)
    if domain == "professional":
        if crunch_mode:
            windows = [(base_date.replace(hour=8, minute=0), base_date.replace(hour=20, minute=0))]
        else:
            windows = [(base_date.replace(hour=9, minute=0), base_date.replace(hour=17, minute=0))]
    else:
        if crunch_mode:
            windows = [(base_date.replace(hour=5, minute=0), base_date.replace(hour=23, minute=0))]
        else:
            windows = [
                (base_date.replace(hour=6, minute=0), base_date.replace(hour=8, minute=0)),
                (base_date.replace(hour=18, minute=0), base_date.replace(hour=21, minute=0))
            ]

    # 2. Collect ALL relevant events (sorted by start time)
    # Including events from other days that might overlap with our windows due to buffer
    relevant_events = []
    for e in events:
        relevant_events.append(parse_event_times(e))
    relevant_events.sort()

    # 3. Search within allowed windows
    for win_start, win_end in windows:
        current_ptr = win_start
        
        for event_start, event_end in relevant_events:
            # Buffer must exist BEFORE and AFTER every event
            eff_event_start = event_start - timedelta(minutes=buffer)
            eff_event_end = event_end + timedelta(minutes=buffer)

            if eff_event_end <= win_start: continue
            if eff_event_start >= win_end: break
            
            # Check gap between current_ptr and the START of the next event's influence
            if (eff_event_start - current_ptr).total_seconds() / 60 >= duration:
                return format_event_time(current_ptr)
            
            current_ptr = max(current_ptr, eff_event_end)
            
        # Check remaining space after last event in window
        if (win_end - current_ptr).total_seconds() / 60 >= duration:
            return format_event_time(current_ptr)

    # Fallback: Try Crunch Mode if not already in it
    if not crunch_mode:
        return find_available_slot(events, duration, date_str, domain, buffer, crunch_mode=True)

    return None

def move_to_next_day(state, event_type, buffer=15, max_lookahead=7, max_daily_events=6):
    """
    Moves an event to the FIRST available day that isn't overcrowded 
    AND doesn't create a Rigid Deadlock (Future-Peeking).
    """
    new_state = copy.deepcopy(state)
    events = new_state.get("events", [])
    
    target_idx = next((i for i, e in enumerate(events) if e["type"] == event_type), None)
    if target_idx is None:
        return state, {"status": "event_not_found"}
    
    target_event = events[target_idx]
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
            # --- FUTURE PEEKING ---
            # Simulate the move and check for rigid deadlocks
            temp_events = copy.deepcopy(events)
            temp_events[target_idx]["date"] = candidate_str
            temp_events[target_idx]["time"] = slot
            
            # Check for rigid conflicts on the candidate day
            rigid_deadlock = False
            for j in range(len(temp_events)):
                if j == target_idx or temp_events[j]["date"] != candidate_str: continue
                
                s1, e1 = parse_event_times(temp_events[target_idx])
                s2, e2 = parse_event_times(temp_events[j])
                
                if s1 < e2 and s2 < e1:
                    if temp_events[target_idx].get("priority") == "high" and not temp_events[target_idx].get("flexible") and \
                       temp_events[j].get("priority") == "high" and not temp_events[j].get("flexible"):
                        rigid_deadlock = True
                        break
            
            if not rigid_deadlock:
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
    Resolves conflict by shrinking duration AND shifting start time if necessary.
    """
    new_state = copy.deepcopy(state)
    events = new_state.get("events", [])
    
    target_idx = next((i for i, e in enumerate(events) if e["type"] == event_type), None)
    if target_idx is None:
        return state, {"status": "event_not_found"}

    target = events[target_idx]
    t_start, t_end = parse_event_times(target)
    
    new_t_start, new_t_end = t_start, t_end
    
    for i, other in enumerate(events):
        if i == target_idx or other.get("date") != target.get("date"):
            continue
            
        o_start, o_end = parse_event_times(other)
        
        # Calculate overlap
        overlap_start = max(new_t_start, o_start)
        overlap_end = min(new_t_end, o_end)
        
        if overlap_start < overlap_end:
            # We have a collision.
            # Strategy: If overlap is at the START of target, shift target start forward.
            # If overlap is at the END of target, shrink duration.
            
            if o_start <= new_t_start < o_end:
                # Overlap at start
                shift = (o_end - new_t_start).total_seconds() / 60
                new_t_start = o_end
            elif o_start < new_t_end <= o_end:
                # Overlap at end
                # Just handled by new_t_end being restricted below
                pass

            # Recalculate duration based on remaining window if possible
            # But the requirement was: original_duration - overlap
            # Let's just ensure they don't touch.
            if new_t_start < o_start:
                # other is after target
                new_t_end = min(new_t_end, o_start)
            elif o_end <= new_t_start:
                # other is before target
                pass

    # Update event with new times
    final_duration = (new_t_end - new_t_start).total_seconds() / 60
    if final_duration < 15:
        return state, {"status": "event_too_short_to_split"}

    events[target_idx]["time"] = format_event_time(new_t_start)
    events[target_idx]["duration"] = int(final_duration)
    events[target_idx]["type"] += " (Partial)"
    events[target_idx]["status"] = "partial_attendance"
    
    return new_state, {"status": "success", "new_duration": int(final_duration)}

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
