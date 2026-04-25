import sys
import os
import random
import matplotlib.pyplot as plt

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.environment import AMALSEnvironment

def run_baseline(num_episodes=100, mode="random", learned_strategy=None):
    env = AMALSEnvironment()
    episode_rewards = []
    
    PLANNING_ACTIONS = ["attend_meeting", "attend_dinner", "balance_both"]
    RECOVERY_ACTIONS = ["reschedule_meeting", "delay_dinner", "send_apology_email"]
    
    print(f"Running {num_episodes} episodes in {mode} mode...")

    for _ in range(num_episodes):
        state = env.reset()
        done = False
        total_reward = 0
        
        while not done:
            step_num = state["step"]
            
            if mode == "random":
                if step_num == 0: action = random.choice(PLANNING_ACTIONS)
                elif step_num == 2: action = random.choice(RECOVERY_ACTIONS)
                else: action = state["last_decision"]
            else:
                # Learned Greedy Policy
                if step_num == 0: action = learned_strategy['plan']
                elif step_num == 2: action = learned_strategy['recovery']
                else: action = state["last_decision"]

            state, reward, done, info = env.step({"decision": action})
            total_reward += reward
        
        episode_rewards.append(total_reward)
    
    return sum(episode_rewards) / num_episodes, episode_rewards

def main():
    num_episodes = 100
    
    # 1. Run Random Baseline
    avg_random, rewards_random = run_baseline(num_episodes, mode="random")
    
    # 2. Run Learned Policy (Based on our previous training results)
    # We found 'balance_both' -> 'send_apology_email' was the optimal strategy
    learned_strategy = {'plan': 'balance_both', 'recovery': 'send_apology_email'}
    avg_learned, rewards_learned = run_baseline(num_episodes, mode="learned", learned_strategy=learned_strategy)

    # 3. Print Results
    print("\n" + "="*30)
    print("Multi-Step Performance Comparison")
    print("="*30)
    print(f"Random Action Avg Reward:  {avg_random:.3f}")
    print(f"Learned Policy Avg Reward: {avg_learned:.3f}")
    print(f"Performance Lift:          {((avg_learned - avg_random) / abs(avg_random)) * 100:.1f}%")
    print("="*30)

    # 4. Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(rewards_random, label="Random Baseline", color='red', alpha=0.4)
    plt.plot(rewards_learned, label="Learned Policy", color='blue', alpha=0.4)
    
    # Add horizontal lines for averages
    plt.axhline(y=avg_random, color='red', linestyle='--', label=f'Random Avg ({avg_random:.2f})')
    plt.axhline(y=avg_learned, color='blue', linestyle='--', label=f'Learned Avg ({avg_learned:.2f})')
    
    plt.title("Baseline vs. Learned Policy (Multi-Step)")
    plt.xlabel("Episode")
    plt.ylabel("Total Cumulative Reward")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig("baseline_comparison.png")
    print("\nComparison plot saved as: baseline_comparison.png")

if __name__ == "__main__":
    main()
