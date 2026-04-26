import copy
from datetime import datetime, timedelta

def parse_event_times(event):
    """Helper to get start and end datetime objects for an event."""
    try:
        start_dt = datetime.strptime(f"{event['date']} {event['time']}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(minutes=event.get("duration", 60))
        return start_dt, end_dt
    except:
        # Fallback for Malformed Data
        return datetime.now(), datetime.now()

def format_event_time(dt):
    """Helper to convert datetime to HH:MM."""
    return dt.strftime("%H:%M")

def find_available_slot(events, duration, date_str, domain, buffer=15, mode="standard"):
    """
    Finds the first available gap in the schedule.
    Modes: standard, crunch (expanded), emergency (24h)
    
    Level-2 Fixes:
    - Cross-Day Buffer: Uses parse_event_times for ALL events.
    - Domain Paradox: mode='emergency' allows 24h window for long events.
    """
    base_date = datetime.strptime(date_str, "%Y-%m-%d")
    
    # 1. Define Windows based on mode
    if mode == "emergency":
        windows = [(base_date.replace(hour=0, minute=0), base_date.replace(hour=23, minute=59))]
    elif domain == "professional":
        if mode == "crunch":
            windows = [(base_date.replace(hour=8, minute=0), base_date.replace(hour=21, minute=0))]
        else:
            windows = [(base_date.replace(hour=9, minute=0), base_date.replace(hour=17, minute=0))]
    else:
        if mode == "crunch":
            windows = [(base_date.replace(hour=5, minute=0), base_date.replace(hour=23, minute=0))]
        else:
            windows = [
                (base_date.replace(hour=6, minute=0), base_date.replace(hour=8, minute=0)),
                (base_date.replace(hour=18, minute=0), base_date.replace(hour=21, minute=0))
            ]

    # 2. Collect ALL relevant events for cross-day buffer checks
    all_ranges = []
    for e in events:
        all_ranges.append(parse_event_times(e))
    all_ranges.sort()

    # 3. Search Windows
    for win_start, win_end in windows:
        current_ptr = win_start
        
        for event_start, event_end in all_ranges:
            # Buffer influence
            eff_start = event_start - timedelta(minutes=buffer)
            eff_end = event_end + timedelta(minutes=buffer)

            if eff_end <= win_start: continue
            if eff_start >= win_end: break
            
            # Gap Check
            if (eff_start - current_ptr).total_seconds() / 60 >= duration:
                return format_event_time(current_ptr)
            
            current_ptr = max(current_ptr, eff_end)
            
        # End of Window Check
        if (win_end - current_ptr).total_seconds() / 60 >= duration:
            return format_event_time(current_ptr)

    # 4. Fallback escalation
    if mode == "standard":
        return find_available_slot(events, duration, date_str, domain, buffer, mode="crunch")
    elif mode == "crunch":
        return find_available_slot(events, duration, date_str, domain, buffer, mode="emergency")

    return None

def move_to_next_day(state, event_type, buffer=15, max_lookahead=7, max_daily_events=6):
    """
    Moves an event to the FIRST available day (Future-Peeking).
    """
    new_state = copy.deepcopy(state)
    events = new_state.get("events", [])
    
    target_idx = next((i for i, e in enumerate(events) if e["type"] == event_type), None)
    if target_idx is None: return state, {"status": "event_not_found"}
    
    target_event = events[target_idx]
    current_date_obj = datetime.strptime(target_event["date"], "%Y-%m-%d")

    for i in range(1, max_lookahead + 1):
        candidate_date = current_date_obj + timedelta(days=i)
        candidate_str = candidate_date.strftime("%Y-%m-%d")
        
        if len([e for e in events if e.get("date") == candidate_str]) >= max_daily_events:
            continue
            
        slot = find_available_slot(events, target_event.get("duration", 60), candidate_str, target_event.get("domain", "personal"), buffer=buffer)
        
        if slot:
            # Future Peek: Check for deadlocks
            s1 = datetime.strptime(f"{candidate_str} {slot}", "%Y-%m-%d %H:%M")
            e1 = s1 + timedelta(minutes=target_event.get("duration", 60))
            
            rigid_deadlock = False
            for e in events:
                if e.get("date") != candidate_str: continue
                s2, e2 = parse_event_times(e)
                if s1 < e2 and s2 < e1:
                    if target_event.get("priority") == "high" and not target_event.get("flexible") and \
                       e.get("priority") == "high" and not e.get("flexible"):
                        rigid_deadlock = True
                        break
            
            if not rigid_deadlock:
                target_event["date"] = candidate_str
                target_event["time"] = slot
                target_event["status"] = "moved_to_future_day"
                return new_state, {"status": "success", "new_date": candidate_str, "new_time": slot}

    return state, {"status": "no_available_days_found"}

def apply_partial_attendance(state, event_type):
    """
    Level-2 Refined: Removes full overlap from both sides.
    """
    new_state = copy.deepcopy(state)
    events = new_state.get("events", [])
    target_idx = next((i for i, e in enumerate(events) if e["type"] == event_type), None)
    if target_idx is None: return state, {"status": "event_not_found"}

    target = events[target_idx]
    t_start, t_end = parse_event_times(target)
    new_t_start, new_t_end = t_start, t_end
    
    for i, other in enumerate(events):
        if i == target_idx or other.get("date") != target.get("date"): continue
        o_start, o_end = parse_event_times(other)
        
        # Calculate overlap and trim
        if max(new_t_start, o_start) < min(new_t_end, o_end):
            if o_start <= new_t_start < o_end: new_t_start = o_end
            if o_start < new_t_end <= o_end: new_t_end = o_start

    duration = (new_t_end - new_t_start).total_seconds() / 60
    if duration < 15: return state, {"status": "event_too_short"}

    events[target_idx]["time"] = format_event_time(new_t_start)
    events[target_idx]["duration"] = int(duration)
    events[target_idx]["status"] = "partial_attendance"
    return new_state, {"status": "success", "new_duration": int(duration)}

def detect_conflicts(state):
    events = state.get("events", [])
    conflicts = []
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            s1, e1 = parse_event_times(events[i])
            s2, e2 = parse_event_times(events[j])
            if s1 < e2 and s2 < e1:
                conflicts.append((events[i]["type"], events[j]["type"]))
    return conflicts

def reschedule_event(state, event_type, new_time):
    new_state = copy.deepcopy(state)
    for event in new_state.get("events", []):
        if event["type"] == event_type:
            event["time"] = new_time
            event["status"] = "rescheduled"
            return new_state, {"status": "success", "new_time": new_time}
    return state, {"status": "not_found"}
