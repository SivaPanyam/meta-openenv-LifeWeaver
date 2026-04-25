import sys
import os
from collections import Counter

# Add current directory to path for imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from env.environment import AMALSEnvironment

def run_episode(env, actions):
    """Utility to run a full episode with a list of actions."""
    env.reset()
    total_reward = 0
    history = []
    
    for action_name in actions:
        state, reward, done, info = env.step({"decision": action_name})
        total_reward += reward
        history.append({
            "step": env.step_count,
            "action": action_name,
            "phase": info.get("phase"),
            "outcome": info["outcome"],
            "reward": reward,
            "done": done,
            "state": state
        })
    return total_reward, history

def test_full_episode():
    print("--- TEST 1: FULL EPISODE EXECUTION ---")
    env = AMALSEnvironment()
    actions = ["balance_both", "balance_both", "send_apology_email"]
    
    total_reward, history = run_episode(env, actions)
    
    for entry in history:
        print(f"Step {entry['step']} | Phase: {entry['phase']:<10} | Action: {entry['action']:<20} | Outcome: {str(entry['outcome']):<8} | Reward: {entry['reward']:.2f}")
    
    print(f"Final Total Reward: {total_reward:.2f}\n")

def test_uncertainty():
    print("--- TEST 2: MULTI-RUN UNCERTAINTY TEST ---")
    env = AMALSEnvironment()
    actions = ["balance_both", "balance_both", "send_apology_email"]
    outcomes = []
    
    NUM_RUNS = 20
    for i in range(NUM_RUNS):
        _, history = run_episode(env, actions)
        # Outcome is decided in Step 1 (execution phase)
        outcomes.append(history[1]["outcome"])
    
    print(f"Outcomes across {NUM_RUNS} runs: {dict(Counter(outcomes))}")
    print("Expected: Mix of success/partial/failure.\n")

def test_recovery_effectiveness():
    print("--- TEST 3: RECOVERY EFFECTIVENESS ---")
    env = AMALSEnvironment()
    
    # Case A: No recovery
    actions_a = ["balance_both", "balance_both", "balance_both"]
    # Case B: With recovery
    actions_b = ["balance_both", "balance_both", "send_apology_email"]
    
    rewards_a = []
    rewards_b = []
    
    # Run 20 times for statistical significance
    NUM_RUNS = 20
    for _ in range(NUM_RUNS):
        rewards_a.append(run_episode(env, actions_a)[0])
        rewards_b.append(run_episode(env, actions_b)[0])
        
    avg_a = sum(rewards_a) / len(rewards_a)
    avg_b = sum(rewards_b) / len(rewards_b)
    
    print(f"Avg reward WITHOUT recovery (Case A): {avg_a:.3f}")
    print(f"Avg reward WITH recovery (Case B):    {avg_b:.3f}")
    print(f"Improvement: {avg_b - avg_a:.3f}")

def test_progression_and_state():
    print("\n--- TEST 4 & 5: PROGRESSION AND STATE UPDATES ---")
    env = AMALSEnvironment()
    env.reset()
    
    # Step 0
    s0, r0, d0, i0 = env.step({"decision": "balance_both"})
    print(f"Step {env.step_count}: done={d0}, state_step={s0['step']}, last_decision={s0['last_decision']}")
    assert d0 == False
    
    # Step 1
    s1, r1, d1, i1 = env.step({"decision": "balance_both"})
    print(f"Step {env.step_count}: done={d1}, state_step={s1['step']}, outcome={s1['outcome']}")
    assert d1 == False
    
    # Step 2
    s2, r2, d2, i2 = env.step({"decision": "send_apology_email"})
    print(f"Step {env.step_count}: done={d2}, state_step={s2['step']}, outcome={s2['outcome']}")
    assert d2 == True
    
    print("Progression and State Checks: PASS\n")

if __name__ == "__main__":
    test_full_episode()
    test_uncertainty()
    test_recovery_effectiveness()
    test_progression_and_state()
