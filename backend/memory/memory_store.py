import json
import os

MEMORY_FILE = "backend/memory/memory.json"

def load_memory():
    """Loads the memory file, creating it if it doesn't exist."""
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_experience(experience):
    """
    Appends a new experience to the memory.
    Format: {state_summary, decision, action, outcome, reward}
    """
    memory = load_memory()
    memory.append(experience)
    
    # Keep memory size manageable (last 100 experiences)
    if len(memory) > 100:
        memory = memory[-100:]
        
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory, f, indent=2)

def get_best_action_from_memory(state_summary):
    """
    Looks for similar past states and identifies the action with the highest average reward.
    """
    memory = load_memory()
    similar_cases = [m for m in memory if m["state_summary"] == state_summary]
    
    if not similar_cases:
        return None

    # Aggregate rewards per action
    action_stats = {}
    for case in similar_cases:
        action = case["decision"]
        reward = case.get("reward", 0)
        if action not in action_stats:
            action_stats[action] = []
        action_stats[action].append(reward)
    
    # Calculate averages and pick the best
    averages = {a: (sum(r)/len(r)) for a, r in action_stats.items()}
    best_action = max(averages, key=averages.get)
    
    # Return the best action if it has any positive reward
    if averages[best_action] > 0.1:
        return best_action
    return None
