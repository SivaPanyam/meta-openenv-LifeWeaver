import sys
import os

# Ensure tools can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .calendar_tool import reschedule_event, find_available_slot, move_to_next_day, apply_partial_attendance
from .email_tool import send_email

def execute_tool(decision_input, state):
    """
    Central dispatcher capable of executing sequential or composite actions.
    Supports single action dict or list of action dicts.
    Returns: (updated_state, primary_response, tools_used_list)
    """
    current_state = state
    tools_used = []
    primary_response = None
    
    # Standardize input to list
    if isinstance(decision_input, dict):
        # Check if it contains 'final_actions' list
        actions = decision_input.get("final_actions", [])
        if not actions and "action" in decision_input:
            actions = [decision_input]
    else:
        actions = decision_input

    # Realistic scheduling: Use travel_time as buffer
    travel_time = state.get("travel_time", 15)

    for action_dict in actions:
        events = current_state.get("events", [])
        action = action_dict.get("action")
        target = action_dict.get("target")
        
        if not action or action == "no_change": continue
        print(f"Executing tool: {action} on {target}")

        if action == "reschedule":
            target_event = next((e for e in events if e["type"] == target), None)
            if not target_event: continue
            
            new_time = find_available_slot(events, target_event.get("duration", 60), target_event.get("date"), target_event.get("domain", "personal"), buffer=travel_time)
            
            if new_time:
                current_state, resp = reschedule_event(current_state, target, new_time)
                tools_used.append("calendar.reschedule")
                if not primary_response: primary_response = resp
            else:
                current_state, resp = move_to_next_day(current_state, target, buffer=travel_time)
                tools_used.append("calendar.move_to_next_day")
                if not primary_response: primary_response = resp
                
        elif action == "move_to_next_day":
            current_state, resp = move_to_next_day(current_state, target, buffer=travel_time)
            tools_used.append("calendar.move_to_next_day")
            if not primary_response: primary_response = resp

        elif action == "partial_attend":
            current_state, resp = apply_partial_attendance(current_state, target)
            tools_used.append("calendar.partial_attend")
            if not primary_response: primary_response = resp

        elif action == "delay_meeting":
            target_event = next((e for e in events if e["type"] == target), None)
            if not target_event: continue
            new_time = find_available_slot(events, target_event.get("duration", 60), target_event.get("date"), target_event.get("domain", "personal"), buffer=travel_time)
            
            if new_time:
                current_state, resp = reschedule_event(current_state, target, new_time)
                tools_used.append("calendar.delay")
                if not primary_response: primary_response = resp
            else:
                current_state, resp = move_to_next_day(current_state, target, buffer=travel_time)
                tools_used.append("calendar.move_to_next_day")
                if not primary_response: primary_response = resp

        elif action == "skip_event":
            current_state["events"] = [e for e in current_state.get("events", []) if e["type"] != target]
            tools_used.append("calendar.skip")
            resp = {"status": "success", "message": f"Event {target} skipped"}
            if not primary_response: primary_response = resp

        elif action == "escalate_conflict":
            # No state change, but log tool use
            tools_used.append("escalate_to_user")
            resp = {"status": "escalated", "message": f"Conflict {target} escalated"}
            if not primary_response: primary_response = resp

    # Secondary Action (legacy support)
    if isinstance(decision_input, dict) and decision_input.get("secondary_action") == "send_email":
        message = f"Automatic update to resolve scheduling conflicts."
        email_resp = send_email(message)
        tools_used.append("email.send")

    # If no tools were run
    if not tools_used:
        return state, {"status": "no_tool_executed"}, []
        
    return current_state, primary_response, tools_used
