import json
import os

def convert_memory_to_dataset():
    memory_path = "backend/memory/memory.json"
    output_path = "backend/training/dataset.json"
    
    if not os.path.exists(memory_path):
        print(f"Error: {memory_path} not found.")
        return

    with open(memory_path, "r") as f:
        memory_data = json.load(f)

    # Filter: keep only high reward (>0.7)
    # Convert to {"input": "state_summary", "output": "decision"}
    dataset = []
    for entry in memory_data:
        if entry.get("reward", 0) > 0.7:
            # Flatten features and state_summary into a single input dict
            features = entry.get("features", {})
            features["state_summary"] = entry.get("state_summary")
            
            dataset.append({
                "input": features,
                "output": entry.get("decision")
            })

    # Ensure directories exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(dataset, f, indent=2)
    
    print(f"✅ Successfully converted {len(dataset)} high-quality entries to {output_path}")

if __name__ == "__main__":
    convert_memory_to_dataset()
