from calendar_tool import find_available_slot

def test_domain_slots():
    print("=== Testing Domain-Aware Slot Selection ===\n")
    
    events = [
        {"type": "sync", "date": "2026-04-26", "time": "09:00", "duration": 60, "domain": "professional"},
        {"type": "sync2", "date": "2026-04-26", "time": "10:30", "duration": 60, "domain": "professional"}
    ]

    # Test 1: Professional event (should find 12:00 or similar within 9-17)
    # 09:00-10:00, 10:30-11:30 taken. Gap at 10:00 (30 mins). If duration=60, should skip.
    print(f">> Prof (60m): {find_available_slot(events, 60, '2026-04-26', 'professional')}") # Expected: 11:45 (11:30 + 15)

    # Test 2: Personal event (should land in 18:00+ window)
    print(f">> Pers (60m): {find_available_slot(events, 60, '2026-04-26', 'personal')}") # Expected: 06:00 (first morning window)

    # Test 3: Full Professional day
    full_events = []
    for h in range(9, 17):
        full_events.append({"date": "2026-04-26", "time": f"{h:02d}:00", "duration": 45, "domain": "professional"})
    
    print(f">> Prof Full (60m): {find_available_slot(full_events, 60, '2026-04-26', 'professional')}") # Expected: None

if __name__ == "__main__":
    test_domain_slots()
