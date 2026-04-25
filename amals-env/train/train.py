import sys
import os
import random
import matplotlib.pyplot as plt
from collections import Counter

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.environment import AMALSEnvironment

def run_random_baseline(num_episodes=100):
    """Run a random baseline to compare against learning."""
    env = AMALSEnvironment()
    total_rewards = 0
    decisions = ["attend_meeting", "attend_dinner", "balance_both"]
    
    for _ in range(num_episodes):
        env.reset()
        action = {"decision": random.choice(decisions)}
        _, reward, _, _ = env.step(action)
        total_rewards += reward
    
    return total_rewards / num_episodes

def run_training(num_episodes=100, exploration_limit=30, reward_mode="normal", silent=False):
    """
    Trains an agent and returns the best learned action and reward history.
    reward_mode: "normal" (default env) or "test" (artificially boosts 'attend_meeting')
    """
    env = AMALSEnvironment()
    reward_history = {
        "attend_meeting": [],
        "attend_dinner": [],
        "balance_both": []
    }
    episode_rewards = []
    action_distribution = []
    decisions = list(reward_history.keys())

    if not silent:
        print(f"\n>> Starting Training (Mode: {reward_mode})")

    for i in range(num_episodes):
        env.reset()
        
        # Action Selection
        if i < exploration_limit:
            action_name = random.choice(decisions)
        else:
            averages = {action: (sum(rewards) / len(rewards) if rewards else 0) 
                        for action, rewards in reward_history.items()}
            action_name = max(averages, key=averages.get)

        action = {"decision": action_name}
        action_distribution.append(action_name)
        
        # Step the environment
        _, reward, _, _ = env.step(action)

        # Reward Manipulation Test
        if reward_mode == "test":
            if action_name == "attend_meeting":
                reward = 1.0  # Force this to be the winner
            else:
                reward = 0.1

        reward_history[action_name].append(reward)
        episode_rewards.append(reward)

    # Determine Best Action
    final_averages = {action: (sum(rewards) / len(rewards) if rewards else 0) 
                      for action, rewards in reward_history.items()}
    best_action = max(final_averages, key=final_averages.get)
    
    return best_action, episode_rewards, action_distribution, final_averages

def test_exploitation(best_action, num_episodes=20):
    """Test the agent's performance using ONLY the learned best action."""
    env = AMALSEnvironment()
    rewards = []
    print(f"\n>> Validation: Exploitation-Only Test (Action: {best_action})")
    
    for i in range(num_episodes):
        env.reset()
        _, reward, _, _ = env.step({"decision": best_action})
        rewards.append(reward)
        print(f"  Episode {i+1}: Reward = {reward:.2f}")
    
    avg_reward = sum(rewards) / len(rewards)
    print(f"Exploitation Average: {avg_reward:.2f}")
    return avg_reward

def run_validation_suite():
    # 1. Reproducibility Test
    print("--- REPRODUCIBILITY TEST ---")
    best1, _, _, _ = run_training(silent=True)
    best2, _, _, _ = run_training(silent=True)
    print(f"Run 1 Best Action: {best1}")
    print(f"Run 2 Best Action: {best2}")
    if best1 == best2:
        print("RESULT: PASS (Consistent learning)")
    else:
        print("RESULT: FAIL (Inconsistent learning)")

    # 2. Main Training Run
    print("\n--- MAIN TRAINING RUN ---")
    best_action, episode_rewards, dist, averages = run_training()
    
    # Decision Distribution
    counts = Counter(dist)
    print(f"Action Distribution: {dict(counts)}")

    # 3. Baseline Comparison
    print("\n--- BASELINE COMPARISON ---")
    random_avg = run_random_baseline()
    learned_avg = sum(episode_rewards) / len(episode_rewards)
    print(f"Random Avg Reward:  {random_avg:.3f}")
    print(f"Learned Avg Reward: {learned_avg:.3f}")
    print(f"Improvement: {((learned_avg - random_avg) / random_avg) * 100:.1f}%")

    # 4. Exploitation Test
    test_exploitation(best_action)

    # 5. Reward Manipulation (Test Mode)
    print("\n--- REWARD MANIPULATION TEST ---")
    print("Goal: Force 'attend_meeting' to be the best and see if agent adapts.")
    test_best, _, _, _ = run_training(reward_mode="test")
    print(f"Best Action Learned (Modified Reward): {test_best}")
    if test_best == "attend_meeting":
        print("RESULT: PASS (Agent adapted to reward change)")
    else:
        print("RESULT: FAIL (Agent did not adapt)")

    # 6. Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(episode_rewards, label="Learned Policy")
    plt.axhline(y=random_avg, color='gray', linestyle='--', label='Random Baseline')
    plt.axvline(x=30, color='r', linestyle='--', label='Exploitation Start')
    plt.title("Learning Validation Curve")
    plt.xlabel("Episode")
    plt.ylabel("Reward")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig("reward_plot.png")
    print("\nValidation Plot saved to: reward_plot.png")

if __name__ == "__main__":
    run_validation_suite()
