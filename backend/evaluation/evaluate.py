import sys
import os
import random
import json
from collections import Counter

# Add amals-env and backend to path
sys.path.append(os.path.join(os.getcwd(), "amals-env"))
sys.path.append(os.path.join(os.getcwd(), "backend"))

from env.environment import AMALSEnvironment
from agents.interaction import run_multi_agent
from tools.tool_manager import execute_tool
from memory.memory_store import save_experience

def run_simulation(num_episodes=50, use_memory=True):
    env = AMALSEnvironment()
    results = []
    
    print(f">> Running {num_episodes} episodes (Memory: {use_memory})...")
    
    for _ in range(num_episodes):
        # 1. Reset Environment
        state = env.reset()
        initial_events = state["events"]
        episode_reward = 0
        done = False
        final_decision_made = "none"
        
        # 2. Episode Loop (3 steps: Planning, Execution, Recovery)
        while not done:
            # Action selection
            agent_result = run_multi_agent(state)
            decision = agent_result["final_action"]
            
            # Execute tool to update state (simulating backend integration)
            state, tool_resp, tools_used = execute_tool(decision, state)
            
            # Step the actual environment
            state, reward, done, info = env.step(decision)
            episode_reward += reward
            
            if info["step"] == 1: # Step count 1 in env corresponds to planning phase exit
                final_decision_made = decision.get("action", "no_change")

        # 3. Save experience IF memory is enabled
        if use_memory:
            prof_high = any(e for e in initial_events if e["domain"] == "professional" and e["priority"] == "high")
            pers_high = any(e for e in initial_events if e["domain"] == "personal" and e["priority"] == "high")
            summary = "complex_high_conflict" if (prof_high and pers_high) else "standard_conflict"
            
            save_experience({
                "state_summary": summary,
                "decision": final_decision_made,
                "reward": episode_reward
            })
            
        results.append({
            "reward": episode_reward,
            "decision": final_decision_made,
            "conflict": env.has_conflict
        })
        
    return results

def calculate_metrics(results):
    avg_reward = sum(r["reward"] for r in results) / len(results)
    success_rate = (sum(1 for r in results if r["reward"] > 0.5) / len(results)) * 100
    resolution_rate = (sum(1 for r in results if r["conflict"] and r["decision"] != "no_change") / max(1, sum(1 for r in results if r["conflict"]))) * 100
    
    decisions = Counter([r["decision"] for r in results])
    strategy_diversity = len(decisions)
    best_strategy = decisions.most_common(1)[0][0] if decisions else "none"
    
    return {
        "avg_reward": avg_reward,
        "success_rate": success_rate,
        "resolution_rate": resolution_rate,
        "best_strategy": best_strategy,
        "diversity": strategy_diversity
    }

def run_evaluation():
    MEMORY_FILE = "backend/memory/memory.json"
    if os.path.exists(MEMORY_FILE): os.remove(MEMORY_FILE)
    
    # 1. Run Baseline (Without Memory)
    print("--- BASELINE EVALUATION (NO MEMORY) ---")
    results_no_mem = run_simulation(50, use_memory=False)
    metrics_no_mem = calculate_metrics(results_no_mem)
    
    # 2. Run Learning (With Memory)
    print("\n--- LEARNING EVALUATION (WITH MEMORY) ---")
    run_simulation(30, use_memory=True) # Pre-populate
    results_mem = run_simulation(50, use_memory=True)
    metrics_mem = calculate_metrics(results_mem)
    
    # 3. Output Comparison
    print("\n" + "="*40)
    print("=== SYSTEM PERFORMANCE EVALUATION ===")
    print("="*40)
    print(f"METRIC            | NO MEMORY | WITH MEMORY")
    print(f"-----------------------------------------")
    print(f"Avg Reward        | {metrics_no_mem['avg_reward']:.3f}     | {metrics_mem['avg_reward']:.3f}")
    print(f"Success Rate      | {metrics_no_mem['success_rate']:.1f}%     | {metrics_mem['success_rate']:.1f}%")
    print(f"Resolution Rate   | {metrics_no_mem['resolution_rate']:.1f}%     | {metrics_mem['resolution_rate']:.1f}%")
    print(f"Best Strategy     | {metrics_no_mem['best_strategy']} | {metrics_mem['best_strategy']}")
    print(f"Strategy Diversity| {metrics_no_mem['diversity']}         | {metrics_mem['diversity']}")
    
    improvement = ((metrics_mem['avg_reward'] - metrics_no_mem['avg_reward']) / abs(metrics_no_mem['avg_reward'])) * 100
    print(f"\n>> PERFORMANCE IMPROVEMENT: {improvement:+.1f}%")
    print("="*40)

if __name__ == "__main__":
    run_evaluation()
