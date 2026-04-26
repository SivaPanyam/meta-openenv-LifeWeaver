import sys
import os
import requests
import time

# Simulation helper
def validate_phase4():
    print("=== Phase 4 (Explanation Layer) Validation ===\n")
    
    BASE_URL = "http://127.0.0.1:8000"
    
    # 1. Ensure Backend is Up
    try:
        requests.get(f"{BASE_URL}/")
    except:
        print("❌ FAILED: Backend not accessible. Ensure server.py is running.")
        return

    # 2. Reset to get fresh state
    print(">> Resetting environment...")
    requests.get(f"{BASE_URL}/reset")
    
    # 3. Call Optimize
    print(">> Calling POST /optimize...")
    resp = requests.post(f"{BASE_URL}/optimize")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: API returned status {resp.status_code}")
        return
        
    data = resp.json()
    
    # 4. START STRICT CHECKLIST
    results = {
        "structure": False,
        "conflict": False,
        "opinions": False,
        "decision": False,
        "tracking": False
    }
    
    explanation = data.get("explanation")
    
    # Check 1: Structure
    if explanation and all(k in explanation for k in ["conflict_detected", "conflict_events", "agent_opinions", "final_decision", "action_taken", "state_change"]):
        results["structure"] = True
        print("✅ PASS: Explanation structure is valid.")
    else:
        print("❌ FAIL: Missing mandatory keys in explanation object.")

    # Check 2: Conflict Detection
    # (Note: conflict_detected depends on state, but keys must exist)
    if isinstance(explanation.get("conflict_detected"), bool) and isinstance(explanation.get("conflict_events"), list):
        results["conflict"] = True
        print(f"✅ PASS: Conflict detection engine active (Detected: {explanation['conflict_detected']}).")
    else:
        print("❌ FAIL: Conflict detection types are incorrect.")

    # Check 3: Agent Opinions
    ops = explanation.get("agent_opinions", {})
    required_agents = ["calendar", "career", "social", "email"]
    if all(agent in ops for agent in required_agents):
        results["opinions"] = True
        print(f"✅ PASS: All {len(required_agents)} agent opinions captured.")
    else:
        missing = [a for a in required_agents if a not in ops]
        print(f"❌ FAIL: Missing opinions from: {missing}")

    # Check 4: Decision Consistency
    decision = explanation.get("final_decision", {})
    action_taken = explanation.get("action_taken", [])
    
    if decision.get("action") == "no_change":
        if not action_taken:
            results["decision"] = True
            print("✅ PASS: Decision 'no_change' matches empty action log.")
    elif decision.get("action"):
        if action_taken:
            results["decision"] = True
            print(f"✅ PASS: Decision '{decision['action']}' matches action log {action_taken}.")
    
    # Check 5: State Change Tracking
    change = explanation.get("state_change", {})
    if "before" in change and "after" in change:
        before = len(change["before"])
        after = len(change["after"])
        if before > 0 and after > 0:
            results["tracking"] = True
            print(f"✅ PASS: State change snapshots captured ({before} events).")
        else:
            print("❌ FAIL: Snapshots are empty.")
    else:
        print("❌ FAIL: Missing before/after keys in state_change.")

    print("\n" + "="*30)
    print("=== PHASE 4 VALIDATION ===")
    print("="*30)
    print(f"✔ Explanation structure: {'PASS' if results['structure'] else 'FAIL'}")
    print(f"✔ Conflict detection:   {'PASS' if results['conflict'] else 'FAIL'}")
    print(f"✔ Agent opinions:       {'PASS' if results['opinions'] else 'FAIL'}")
    print(f"✔ Decision consistency:  {'PASS' if results['decision'] else 'FAIL'}")
    print(f"✔ State change tracking: {'PASS' if results['tracking'] else 'FAIL'}")
    print("="*30)

if __name__ == "__main__":
    validate_phase4()
