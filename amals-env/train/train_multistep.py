import sys
import os
import random
import matplotlib.pyplot as plt
from collections import Counter

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.environment import AMALSEnvironment

def train_multistep():
    env = AMALSEnvironment()
    num_episodes = 200
    exploration_limit = 50
    
    # Action Pools
    PLANNING_ACTIONS = ["attend_meeting", "attend_dinner", "balance_both"]
    RECOVERY_ACTIONS = ["reschedule_meeting", "delay_dinner", "send_apology_email"]
    
    # Learning tracking
    # We'll track rewards per planning action (Step 0) and recovery action (Step 2)
    plan_rewards = {a: [] for a in PLANNING_ACTIONS}
    recovery_rewards = {a: [] for a in RECOVERY_ACTIONS}
    
    # Stats tracking
    episode_rewards = []
    outcomes = []
    recovery_count = 0
    
    print(f"Starting Multi-Step Training for {num_episodes} episodes...")

    for i in range(num_episodes):
        state = env.reset()
        done = False
        total_reward = 0
        
        # Actions chosen this episode
        chosen_plan = None
        chosen_recovery = None
        
        while not done:
            step_num = state["step"]
            
            # 1. Action Selection Logic
            if i < exploration_limit:
                # EXPLORATION: Random actions
                if step_num == 0:
                    action_name = random.choice(PLANNING_ACTIONS)
                elif step_num == 2:
                    action_name = random.choice(RECOVERY_ACTIONS)
                else:
                    action_name = state["last_decision"] # Default for execution phase
            else:
                # EXPLOITATION: Greedy based on averages
                if step_num == 0:
                    avgs = {a: (sum(r)/len(r) if r else 0) for a, r in plan_rewards.items()}
                    action_name = max(avgs, key=avgs.get)
                elif step_num == 2:
                    avgs = {a: (sum(r)/len(r) if r else 0) for a, r in recovery_rewards.items()}
                    action_name = max(avgs, key=avgs.get)
                else:
                    action_name = state["last_decision"]

            # Record choices for learning update
            if step_num == 0: chosen_plan = action_name
            if step_num == 2: chosen_recovery = action_name

            # 2. Step the Environment
            state, reward, done, info = env.step({"decision": action_name})
            total_reward += reward
            
            # 3. Collect mid-episode info
            if info["step"] == 1: # Outcome is revealed after Step 1 execution (execution phase is index 1)
                outcomes.append(info["outcome"])
            if info["step"] == 2 and action_name in RECOVERY_ACTIONS:
                recovery_count += 1

        # 4. Learning Update (Update totals for the episode's strategy)
        plan_rewards[chosen_plan].append(total_reward)
        if chosen_recovery:
            recovery_rewards[chosen_recovery].append(total_reward)
        
        episode_rewards.append(total_reward)

        # 5. Periodic Logging
        if (i + 1) % 20 == 0:
            avg_reward = sum(episode_rewards[-20:]) / 20
            outcome_dist = Counter(outcomes[-20:])
            print(f"Ep {i+1:3} | Avg R: {avg_reward:5.2f} | Outcomes: {dict(outcome_dist)}")

    # --- Summary Statistics ---
    print("-" * 50)
    print("Training Complete.")
    best_plan = max(plan_rewards, key=lambda k: sum(plan_rewards[k])/len(plan_rewards[k]) if plan_rewards[k] else 0)
    best_rec = max(recovery_rewards, key=lambda k: sum(recovery_rewards[k])/len(recovery_rewards[k]) if recovery_rewards[k] else 0)
    print(f"Learned Best Strategy: {best_plan} -> {best_rec}")
    print(f"Total Recoveries performed: {recovery_count}")

    # --- Plotting ---
    plt.figure(figsize=(10, 6))
    plt.plot(episode_rewards, label="Total Reward per Episode", color='green', alpha=0.6)
    # Moving average
    window = 10
    if len(episode_rewards) >= window:
        mov_avg = [sum(episode_rewards[j:j+window])/window for j in range(len(episode_rewards)-window+1)]
        plt.plot(range(window-1, len(episode_rewards)), mov_avg, label=f"{window}-Ep Moving Avg", color='darkgreen', linewidth=2)
    
    plt.axvline(x=exploration_limit, color='red', linestyle='--', label='Exploitation Start')
    plt.title("Multi-Step RL Training Reward Curve")
    plt.xlabel("Episode")
    plt.ylabel("Total Cumulative Reward")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig("multistep_reward_plot.png")
    print(f"Reward curve saved as: multistep_reward_plot.png")

if __name__ == "__main__":
    train_multistep()
