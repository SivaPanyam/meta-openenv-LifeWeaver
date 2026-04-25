import sys
import os
import random
import matplotlib.pyplot as plt
from collections import Counter

# Add paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from env.environment import AMALSEnvironment

def evaluate():
    env = AMALSEnvironment()
    num_episodes = 200
    exploration_limit = 50
    
    PLANNING_ACTIONS = ["attend_meeting", "attend_dinner", "balance_both"]
    RECOVERY_ACTIONS = ["reschedule_meeting", "delay_dinner", "send_apology_email"]
    
    # Learning state
    plan_rewards = {a: [] for a in PLANNING_ACTIONS}
    recovery_rewards = {a: [] for a in RECOVERY_ACTIONS}
    
    # Metrics tracking
    episode_rewards = []
    outcomes = []
    
    print(f"--- STARTING EVALUATION RUN ({num_episodes} EPISODES) ---")

    for i in range(num_episodes):
        state = env.reset()
        done = False
        total_reward = 0
        chosen_plan = None
        chosen_recovery = None
        
        while not done:
            step_num = state["step"]
            
            # Action Policy (Exploration vs Exploitation)
            if i < exploration_limit:
                if step_num == 0: action_name = random.choice(PLANNING_ACTIONS)
                elif step_num == 2: action_name = random.choice(RECOVERY_ACTIONS)
                else: action_name = state.get("last_decision")
            else:
                if step_num == 0:
                    avgs = {a: (sum(r)/len(r) if r else 0) for a, r in plan_rewards.items()}
                    action_name = max(avgs, key=avgs.get)
                elif step_num == 2:
                    avgs = {a: (sum(r)/len(r) if r else 0) for a, r in recovery_rewards.items()}
                    action_name = max(avgs, key=avgs.get)
                else:
                    action_name = state.get("last_decision")

            if step_num == 0: chosen_plan = action_name
            if step_num == 2: chosen_recovery = action_name

            state, reward, done, info = env.step({"decision": action_name})
            total_reward += reward
            
            if info["step"] == 1: # Execution outcome revealed
                outcomes.append(info["outcome"])

        # Update learning
        plan_rewards[chosen_plan].append(total_reward)
        if chosen_recovery:
            recovery_rewards[chosen_recovery].append(total_reward)
        episode_rewards.append(total_reward)

    # --- CALCULATE METRICS ---
    avg_reward = sum(episode_rewards) / len(episode_rewards)
    max_reward = max(episode_rewards)
    min_reward = min(episode_rewards)
    
    counts = Counter(outcomes)
    success_rate = (counts['success'] / len(outcomes)) * 100
    failure_rate = (counts['failure'] / len(outcomes)) * 100
    partial_rate = (counts['partial'] / len(outcomes)) * 100

    # Baseline comparison (simulated based on randomized start)
    random_avg = sum(episode_rewards[:exploration_limit]) / exploration_limit
    learned_avg = sum(episode_rewards[exploration_limit:]) / (num_episodes - exploration_limit)
    improvement = ((learned_avg - random_avg) / abs(random_avg)) * 100

    best_plan = max(plan_rewards, key=lambda k: sum(plan_rewards[k])/len(plan_rewards[k]) if plan_rewards[k] else 0)
    best_recovery = max(recovery_rewards, key=lambda k: sum(recovery_rewards[k])/len(recovery_rewards[k]) if recovery_rewards[k] else 0)

    # --- OUTPUT SUMMARY ---
    print("\n" + "="*30)
    print("=== MODEL PERFORMANCE ===")
    print("="*30)
    print(f"Average Reward:  {avg_reward:.3f}")
    print(f"Max Reward:      {max_reward:.3f}")
    print(f"Min Reward:      {min_reward:.3f}")
    print(f"Best Strategy:   {best_plan} -> {best_recovery}")
    print("-" * 30)
    print(f"Success Rate:    {success_rate:.1f}%")
    print(f"Partial Rate:    {partial_rate:.1f}%")
    print(f"Failure Rate:    {failure_rate:.1f}%")
    print("-" * 30)
    print(f"Random Baseline: {random_avg:.3f}")
    print(f"Learned Policy:  {learned_avg:.3f}")
    print(f"Improvement:     {improvement:.1f}%")
    print("="*30 + "\n")

    # --- PLOT VISUALS ---
    # 1. Reward Curve
    plt.figure(figsize=(10, 5))
    plt.plot(episode_rewards, color='#6366f1', alpha=0.3)
    # Moving average
    window = 10
    ma = [sum(episode_rewards[j:j+window])/window for j in range(len(episode_rewards)-window+1)]
    plt.plot(range(window-1, len(episode_rewards)), ma, color='#4f46e5', linewidth=2, label='10-Ep Moving Avg')
    plt.axvline(x=exploration_limit, color='red', linestyle='--', label='Exploitation Start')
    plt.title("Reward Evolution")
    plt.xlabel("Episode")
    plt.ylabel("Cumulative Reward")
    plt.legend()
    plt.grid(alpha=0.2)
    plt.savefig("reward_plot.png")

    # 2. Outcome Distribution
    plt.figure(figsize=(8, 5))
    labels = ['Success', 'Partial', 'Failure']
    vals = [success_rate, partial_rate, failure_rate]
    colors = ['#22c55e', '#eab308', '#ef4444']
    plt.bar(labels, vals, color=colors)
    plt.title("Execution Phase Outcome Distribution")
    plt.ylabel("Percentage (%)")
    plt.savefig("outcome_distribution.png")

    print("✅ Visuals saved: reward_plot.png, outcome_distribution.png")

if __name__ == "__main__":
    evaluate()
