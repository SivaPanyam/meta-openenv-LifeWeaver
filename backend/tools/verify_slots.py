from calendar_tool import find_available_slot

def test_slots():
    print("=== Testing Dynamic Slot Selection ===\n")
    
    # Case 1: Early gap
    events1 = [
        {"time": "10:00", "duration": 60}, # Ends 11:00
        {"time": "13:00", "duration": 60}
    ]
    # Expected: 08:00 (default start search)
    print(f"Test 1 (Early gap): {find_available_slot(events1, 60)}")

    # Case 2: Gap between events
    events2 = [
        {"time": "08:00", "duration": 60}, # Ends 09:00
        {"time": "12:00", "duration": 60}
    ]
    # Gap: 09:00 - 12:00 (180 mins). Needs 60.
    # Expected: 09:15 (09:00 + 15 min buffer)
    print(f"Test 2 (Middle gap): {find_available_slot(events2, 60)}")

    # Case 3: No gap, append at end
    events3 = [
        {"time": "08:00", "duration": 480}, # 8 hours, ends 16:00
        {"time": "16:15", "duration": 60}   # ends 17:15
    ]
    # Expected: 17:30 (17:15 + 15 min buffer)
    print(f"Test 3 (Append): {find_available_slot(events3, 60)}")

if __name__ == "__main__":
    test_slots()
