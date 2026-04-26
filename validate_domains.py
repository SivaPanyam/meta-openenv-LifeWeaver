import sys
import os
from collections import Counter

# Add amals-env to path
sys.path.append(os.path.join(os.getcwd(), "amals-env"))

from env.environment import AMALSEnvironment

def validate():
    env = AMALSEnvironment()
    iterations = 50
    samples_to_print = 5
    
    prof_types = ["team_meeting", "client_call", "project_sync", "presentation", "code_review", "deep_work"]
    pers_types = ["family_dinner", "gym", "friend_hangout", "personal_errand", "hobby_time", "doctor_appt"]
    
    results = {
        "domain_field_present": True,
        "domain_values_correct": True,
        "type_mapping_correct": True,
        "time_rules_correct": True,
        "conflicts_found": 0
    }

    print(f"--- VALIDATING {iterations} SCENARIOS ---")

    for i in range(iterations):
        obs = env.reset()
        events = obs.get("events", [])
        
        # Check for conflicts in this scenario
        times = [e["time"] for e in events]
        if len(times) != len(set(times)):
            results["conflicts_found"] += 1
            
        if i < samples_to_print:
            print(f"\nScenario {i+1}:")
            for e in events:
                print(f"  [{e['domain'].upper()}] {e['time']} - {e['type']} (Prio: {e['priority']}, Flex: {e['flexible']})")

        for e in events:
            # 1. Domain Presence
            if "domain" not in e: results["domain_field_present"] = False
            if e.get("domain") not in ["professional", "personal"]: results["domain_values_correct"] = False
            
            # 2. Domain Correctness
            if e["domain"] == "professional" and e["type"] not in prof_types: results["type_mapping_correct"] = False
            if e["domain"] == "personal" and e["type"] not in pers_types: results["type_mapping_correct"] = False
            
            # 3. Time Validation
            hour = int(e["time"].split(":")[0])
            if e["domain"] == "professional":
                if not (9 <= hour <= 17): # Starts between 9 and 17:00
                    print(f"ERROR: Prof event at {e['time']}")
                    results["time_rules_correct"] = False
            else:
                if not (6 <= hour <= 8 or 18 <= hour <= 21): # Starts in personal windows
                    print(f"ERROR: Pers event at {e['time']}")
                    results["time_rules_correct"] = False

    print("\n" + "="*30)
    print("=== DOMAIN SYSTEM VALIDATION ===")
    print("="*30)
    print(f"✔ Domain assignment: {'PASS' if results['domain_field_present'] and results['domain_values_correct'] and results['type_mapping_correct'] else 'FAIL'}")
    print(f"✔ Time rules:        {'PASS' if results['time_rules_correct'] else 'FAIL'}")
    
    conflict_rate = (results["conflicts_found"] / iterations) * 100
    print(f"✔ Conflict realism:  {'PASS' if 30 <= conflict_rate <= 50 else 'FAIL'} ({conflict_rate:.1f}%)")
    print("="*30)

if __name__ == "__main__":
    validate()
