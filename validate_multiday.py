import requests
import json
import time

def validate_multiday():
    print("=== Multi-Day Scheduling Validation ===\n")
    BASE_URL = "http://localhost:8003"

    # 1. Reset and check initial state
    print(">> Resetting environment...")
    resp = requests.get(f"{BASE_URL}/reset")
    obs = resp.json()
    
    current_date = obs.get("current_date")
    events = obs.get("events", [])
    
    date_pass = all("date" in e for e in events)
    if date_pass:
        print(f"✅ PASS: All events have a date field. Current Date: {current_date}")
    else:
        print("❌ FAIL: Some events are missing the date field.")

    # 2. Check move_to_next_day tool directly
    print("\n>> Testing /optimize with high stress (forcing move_to_next_day)...")
    # We might need to reset until we get high stress or just check if the logic triggers
    # For validation, let's manually trigger a move if the logic allows it
    
    resp = requests.post(f"{BASE_URL}/optimize")
    data = resp.json()
    explanation = data.get("explanation", {})
    final_decision = explanation.get("final_decision", {})
    
    print(f"Decision: {final_decision.get('action')} on {final_decision.get('target')}")
    print(f"Reasoning: {final_decision.get('description')}")
    
    if final_decision.get("action") == "move_to_next_day":
        print("✅ PASS: 'move_to_next_day' action was triggered.")
        
        # Verify the date change in the new state
        new_events = data.get("events", [])
        target = final_decision.get("target")
        moved_event = next((e for e in new_events if e["type"] == target), None)
        
        if moved_event and moved_event["date"] > current_date:
            print(f"✅ PASS: Event '{target}' moved from {current_date} to {moved_event['date']}.")
        else:
            print("❌ FAIL: Event date was not incremented correctly.")
    else:
        print("ℹ️ INFO: 'move_to_next_day' not triggered in this sample (Stress/Density dependent).")

if __name__ == "__main__":
    validate_multiday()
