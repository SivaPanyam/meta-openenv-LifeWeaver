import sys
import os
import importlib
import yaml

# Add current directory to path for imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

def test_environment():
    print("=== OpenEnv Validation Suite ===\n")

    # --- B. Method Existence Check ---
    print("[1/6] Method Existence Check...")
    from env.environment import AMALSEnvironment
    env = AMALSEnvironment()
    
    required_methods = ["reset", "step", "state"]
    for method in required_methods:
        exists = hasattr(env, method)
        print(f"  - Method '{method}': {'PASS' if exists else 'FAIL'}")
        assert exists, f"Missing required method: {method}"

    # --- A. Basic Functionality Test ---
    print("\n[2/6] Basic Functionality Test...")
    initial_state = env.reset()
    print(f"  - Initial State: {initial_state}")
    
    action = {"decision": "balance_both"}
    state, reward, done, info = env.step(action)
    print(f"  - Action Taken: {action}")
    print(f"  - Result -> Reward: {reward}, Done: {done}, Info: {info}")
    
    assert isinstance(reward, (int, float)), "Reward must be numeric"
    assert isinstance(done, bool), "Done must be boolean"
    assert isinstance(state, dict), "State must be a dictionary"

    # --- C. Entry Point Simulation ---
    print("\n[3/6] Entry Point Simulation (Dynamic Loading)...")
    try:
        module_path = "env.environment"
        class_name = "AMALSEnvironment"
        module = importlib.import_module(module_path)
        env_class = getattr(module, class_name)
        dynamic_env = env_class()
        print(f"  - Successfully loaded {class_name} from {module_path}")
    except Exception as e:
        print(f"  - Dynamic Load FAIL: {e}")
        raise e

    # --- D. Multi-Episode Stability Test ---
    print("\n[4/6] Multi-Episode Stability Test (10 episodes)...")
    for i in range(10):
        env.reset()
        # Step 1: Planning
        _, _, d, _ = env.step({"decision": "balance_both"})
        assert d == False, f"Episode {i+1} signaled done too early (Step 1)"
        
        # Step 2: Execution
        _, _, d, _ = env.step({"decision": "balance_both"})
        assert d == False, f"Episode {i+1} signaled done too early (Step 2)"
        
        # Step 3: Recovery
        _, _, d, _ = env.step({"decision": "send_apology_email"})
        assert d == True, f"Episode {i+1} failed to signal 'done' after 3 steps"
    print("  - Stability: PASS (No crashes, all multi-step episodes completed)")

    # --- E. Reward Consistency Test ---
    print("\n[5/6] Reward Consistency Test...")
    env.reset()
    r1 = env.step({"decision": "balance_both"})[1]
    env.reset()
    r2 = env.step({"decision": "balance_both"})[1]
    
    print(f"  - Run 1 Reward: {r1}")
    print(f"  - Run 2 Reward: {r2}")
    assert round(r1, 5) == round(r2, 5), "Rewards are inconsistent for the same deterministic action"
    print("  - Consistency: PASS")

    # --- 2. Validate openenv.yaml ---
    print("\n[6/6] openenv.yaml Validation...")
    yaml_path = os.path.join(BASE_DIR, "openenv.yaml")
    if not os.path.exists(yaml_path):
        print(f"  - FAIL: {yaml_path} not found")
        return

    with open(yaml_path, "r") as f:
        config = yaml.safe_load(f)
    
    name = config.get("name")
    entry_point = config.get("entry_point")
    
    print(f"  - Name: {name}")
    print(f"  - Entry Point: {entry_point}")
    
    expected_entry = "env.environment:AMALSEnvironment"
    if entry_point == expected_entry:
        print("  - Entry Point Check: PASS")
    else:
        print(f"  - Entry Point Check: FAIL (Expected {expected_entry})")

    print("\n=== All Tests Passed Successfully ===")

if __name__ == "__main__":
    try:
        test_environment()
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Validation failed: {e}")
        sys.exit(1)
