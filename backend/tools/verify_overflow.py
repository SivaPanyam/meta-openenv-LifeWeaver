from calendar_tool import move_to_next_day
from datetime import datetime

def test_overflow():
    print("=== Testing Lookahead Move Logic ===\n")
    
    # 1. Day 1 is full (6 events)
    events = []
    base_date = "2026-04-26"
    for i in range(6):
        events.append({"type": f"event_{i}", "date": base_date, "time": f"{9+i:02d}:00", "duration": 60})
        
    # 2. Target event to move
    events.append({"type": "movable_task", "date": base_date, "time": "09:00", "duration": 60})
    
    state = {"events": events}
    
    # Run move
    # Day 1 is full, so should move to 2026-04-27
    print(f">> Initial Event Date: {base_date}")
    new_state, resp = move_to_next_day(state, "movable_task", max_daily_events=6)
    
    print(f"Status: {resp['status']}")
    print(f"Moved to: {resp.get('new_date')} at {resp.get('new_time')}")
    print(f"Days Shifted: {resp.get('days_shifted')}")
    
    if resp.get('new_date') == "2026-04-27":
        print("✅ PASS: Correctly skipped overcrowded Day 1.")
    else:
        print("❌ FAIL: Did not skip overcrowded day.")

if __name__ == "__main__":
    test_overflow()
