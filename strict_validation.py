import sys
import os
from datetime import datetime, timedelta
import copy

# Ensure tools can be imported
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "backend"))
sys.path.append(os.path.join(BASE_DIR, "backend", "agents"))
sys.path.append(os.path.join(BASE_DIR, "backend", "tools"))

from backend.tools.calendar_tool import move_to_next_day, find_available_slot, apply_partial_attendance, detect_conflicts, parse_event_times
from backend.agents.coordinator_agent import coordinator_agent

def validate_system():
    results = {}

    print("=== STARTING STRICT VALIDATION ===\n")

    # --- TEST 1: MULTI-DAY (NO SNOWBALL) ---
    print("[TEST 1: MULTI-DAY]")
    events = []
    # Fill Day 1 and Day 2
    for d in ["2026-04-26", "2026-04-27"]:
        for i in range(6):
            events.append({"type": f"full_{d}_{i}", "date": d, "time": f"{9+i:02d}:00", "duration": 45, "domain": "professional"})
    
    events.append({"type": "overflow_task", "date": "2026-04-26", "time": "10:00", "duration": 60, "domain": "personal"})
    state = {"events": events, "travel_time": 15}
    
    new_state, resp = move_to_next_day(state, "overflow_task", max_daily_events=6)
    if resp.get("new_date") == "2026-04-28":
        print("✅ PASS: Correctly skipped two full days and landed on Day 3.")
        results["multi_day"] = "PASS"
    else:
        print(f"❌ FAIL: Moved to {resp.get('new_date')} instead of 2026-04-28.")
        results["multi_day"] = "FAIL"

    # --- TEST 2: DOMAIN RULES ---
    print("\n[TEST 2: DOMAIN RULES]")
    # Prof should land 9-17
    # Pers should land 6-8 or 18-21
    events = [] # Empty day
    p_slot = find_available_slot(events, 60, "2026-04-26", "professional", buffer=15)
    s_slot = find_available_slot(events, 60, "2026-04-26", "personal", buffer=15)
    
    p_pass = "09:00" <= p_slot <= "17:00"
    s_pass = ("06:00" <= s_slot <= "08:00") or ("18:00" <= s_slot <= "21:00")
    
    if p_pass and s_pass:
        print(f"✅ PASS: Prof ({p_slot}) and Personal ({s_slot}) slots respect domain windows.")
        results["domain_rules"] = "PASS"
    else:
        print(f"❌ FAIL: Violation! Prof: {p_slot}, Pers: {s_slot}")
        results["domain_rules"] = "FAIL"

    # --- TEST 3: RIGID DEADLOCK ---
    print("\n[TEST 3: RIGID DEADLOCK]")
    events = [
        {"type": "Rigid 1", "date": "2026-04-26", "time": "10:00", "duration": 60, "priority": "high", "flexible": False},
        {"type": "Rigid 2", "date": "2026-04-26", "time": "10:00", "duration": 60, "priority": "high", "flexible": False}
    ]
    coord_out = coordinator_agent({"events": events, "stress": 0.5, "current_date": "2026-04-26"}, [])
    if coord_out["final_action"]["action"] == "escalate_conflict":
        print("✅ PASS: Deadlock correctly escalated to user.")
        results["deadlock"] = "PASS"
    else:
        print(f"❌ FAIL: System attempted automated fix: {coord_out['final_action']['action']}")
        results["deadlock"] = "FAIL"

    # --- TEST 4: PARTIAL ATTEND ---
    print("\n[TEST 4: PARTIAL ATTEND]")
    # 60 min event at 10:00 vs 60 min event at 10:30 (30 min overlap)
    events = [
        {"type": "Base", "date": "2026-04-26", "time": "10:00", "duration": 60},
        {"type": "Overlapper", "date": "2026-04-26", "time": "10:30", "duration": 60}
    ]
    new_state, resp = apply_partial_attendance({"events": events}, "Overlapper")
    conflicts = detect_conflicts(new_state)
    if not conflicts:
        print("✅ PASS: Overlap successfully removed via duration reduction.")
        results["partial_attend"] = "PASS"
    else:
        print(f"❌ FAIL: Conflicts still remain: {conflicts}")
        results["partial_attend"] = "FAIL"

    # --- TEST 5: DYNAMIC BUFFER ---
    print("\n[TEST 5: DYNAMIC BUFFER]")
    # With 60 min travel_time, an event after 10:00 (ends 11:00) should start >= 12:00
    events = [{"type": "E1", "date": "2026-04-26", "time": "10:00", "duration": 60}]
    slot = find_available_slot(events, 60, "2026-04-26", "professional", buffer=60)
    if slot >= "12:00":
        print(f"✅ PASS: Slot ({slot}) respects 60-min travel buffer.")
        results["buffer"] = "PASS"
    else:
        print(f"❌ FAIL: Buffer ignored or too small: {slot}")
        results["buffer"] = "FAIL"

    # --- TEST 6: MIDNIGHT ROLLOVER ---
    print("\n[TEST 6: MIDNIGHT ROLLOVER]")
    events = [{"type": "Late", "date": "2026-04-26", "time": "23:30", "duration": 90}]
    try:
        start, end = parse_event_times(events[0])
        if end.hour == 1 and end.day == 27:
            print(f"✅ PASS: Cross-day event parsed correctly. Ends: {end}")
            results["midnight"] = "PASS"
        else:
            print(f"❌ FAIL: Cross-day logic wrong. Ends: {end}")
            results["midnight"] = "FAIL"
    except Exception as e:
        print(f"❌ FAIL: Crash during midnight rollover test: {e}")
        results["midnight"] = "FAIL"

    # --- FINAL REPORT ---
    print("\n" + "="*30)
    print("=== SYSTEM VALIDATION REPORT ===")
    print("="*30)
    for key, val in results.items():
        print(f"{key.replace('_', ' ').capitalize():<20}: {val}")
    print("="*30)

if __name__ == "__main__":
    validate_system()
