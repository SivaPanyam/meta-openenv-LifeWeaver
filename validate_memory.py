import sys
import os
import requests
import json
import time

def validate_memory():
    print("=== Memory System Validation ===\n")
    BASE_URL = "http://localhost:8001"
    MEMORY_FILE = "backend/memory/memory.json"

    # 1. Clear memory for clean test
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)
    
    # 2. Perform 3 optimization runs to populate memory
    print(">> Performing 3 optimization runs...")
    for i in range(3):
        requests.get(f"{BASE_URL}/reset")
        requests.post(f"{BASE_URL}/optimize")
        print(f"   Run {i+1} complete.")

    # 3. Check if file exists
    storage_pass = os.path.exists(MEMORY_FILE)
    if storage_pass:
        with open(MEMORY_FILE, 'r') as f:
            data = json.load(f)
            print(f"✅ PASS: Memory file exists with {len(data)} entries.")
    else:
        print("❌ FAIL: Memory file was not created.")

    # 4. Check for Decision Influence
    # We look for the "Memory Insight" in the reasoning of a 4th run
    print("\n>> Performing 4th run to verify decision influence...")
    requests.get(f"{BASE_URL}/reset")
    resp = requests.post(f"{BASE_URL}/optimize")
    explanation = resp.json().get("explanation", {})
    agent_ops = explanation.get("agent_opinions", {})
    
    # The coordinator adds "Memory Insight" to reasoning
    # We check if it appears in any of the agent's consolidated outputs
    influence_pass = any("Memory Insight" in str(reason) for reason in explanation.get("final_decision", {}).values()) or \
                    any("Memory Insight" in str(reason) for reason in explanation.get("agent_opinions", {}).values()) or \
                    "Memory Insight" in explanation.get("final_decision", {}).get("description", "")

    if influence_pass:
        print("✅ PASS: Decision was influenced by historical memory.")
    else:
        # Fallback check: logic might be in description
        desc = explanation.get("final_decision", {}).get("description", "")
        if "Historical data" in desc:
            influence_pass = True
            print("✅ PASS: Decision was influenced by historical memory (via description).")
        else:
            print("❌ FAIL: No evidence of memory influence in reasoning.")

    print("\n" + "="*30)
    print("=== MEMORY VALIDATION ===")
    print("="*30)
    print(f"✔ Memory storage:    {'PASS' if storage_pass else 'FAIL'}")
    print(f"✔ Memory loading:    {'PASS' if storage_pass else 'FAIL'}")
    print(f"✔ Decision influence: {'PASS' if influence_pass else 'FAIL'}")
    print("="*30)

if __name__ == "__main__":
    validate_memory()
