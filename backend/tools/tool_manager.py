import sys
import os

# Ensure tools can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .calendar_tool import reschedule_event, find_available_slot, move_to_next_day, apply_partial_attendance
from .email_tool import send_email

def execute_tool(action_dict, state):
    """
    Central dispatcher capable of executing sequential or composite actions.
    Returns: (updated_state, tool_response, tools_used_list)
    """
    current_state = state
    tools_used = []
    primary_response = None
    events = state.get("events", [])
    
    # Realistic scheduling: Use travel_time as buffer
    travel_time = state.get("travel_time", 15)

    # 1. Primary Action
    action = action_dict.get("action")
    if action:
        print(f"Executing tool: {action}")
    
    if action == "reschedule":
        target = action_dict.get("target")
        # Dynamic slot selection (date-aware + domain-aware + buffer-aware)
        target_event = next((e for e in events if e["type"] == target), {"duration": 60, "date": events[0].get("date") if events else "2026-04-26", "domain": "personal"})
        new_time = find_available_slot(events, target_event.get("duration", 60), target_event.get("date"), target_event.get("domain", "personal"), buffer=travel_time)
        
        if new_time:
            current_state, primary_response = reschedule_event(current_state, target, new_time)
            tools_used.append("calendar.reschedule")
        else:
            # FALLBACK: If no slot today, move to next available day
            print(f"No slot today for {target}, falling back to multi-day move.")
            current_state, primary_response = move_to_next_day(current_state, target, buffer=travel_time)
            tools_used.append("calendar.move_to_next_day")
            
    elif action == "move_to_next_day":
        target = action_dict.get("target")
        current_state, primary_response = move_to_next_day(current_state, target, buffer=travel_time)
        tools_used.append("calendar.move_to_next_day")
    elif action == "partial_attend":
        target = action_dict.get("target")
        current_state, primary_response = apply_partial_attendance(current_state, target)
        tools_used.append("calendar.partial_attend")
    elif action == "delay_meeting":
        target = action_dict.get("target")
        # Dynamic delay (finding next available slot)
        target_event = next((e for e in events if e["type"] == target), {"duration": 60, "date": events[0].get("date") if events else "2026-04-26", "domain": "personal"})
        new_time = find_available_slot(events, target_event.get("duration", 60), target_event.get("date"), target_event.get("domain", "personal"), buffer=travel_time)
        
        if new_time:
            current_state, primary_response = reschedule_event(current_state, target, new_time)
            tools_used.append("calendar.delay")
        else:
            current_state, primary_response = move_to_next_day(current_state, target, buffer=travel_time)
            tools_used.append("calendar.move_to_next_day")
    elif action == "skip_event":
        target = action_dict.get("target")
        current_state["events"] = [e for e in current_state.get("events", []) if e["type"] != target]
        tools_used.append("calendar.skip")
        primary_response = {"status": "success", "message": f"Event {target} skipped"}
        
    # 2. Secondary Action (e.g., from 'balance_both' logic)
    secondary = action_dict.get("secondary_action")
    if secondary == "send_email":
        print(f"Executing secondary tool: {secondary}")
        message = f"Automatic update: '{action_dict.get('target')}' has been rescheduled to resolve a conflict."
        # send_email returns only one dict
        email_resp = send_email(message)
        tools_used.append("email.send")
        if not primary_response:
            primary_response = email_resp

    # If no tools were run
    if not tools_used:
        return state, {"status": "no_tool_executed"}, []
        
    return current_state, primary_response, tools_used
