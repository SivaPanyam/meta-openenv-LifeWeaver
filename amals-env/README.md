# AMALS (Adaptive Multi-Agent Life Simulator)

AMALS is a minimal training environment designed to simulate real-life decision-making scenarios. It follows the OpenEnv-style architecture to provide a standardized interface for training agents on trade-offs and scheduling conflicts.

## Project Structure
- `env/`: Contains the core environment logic (state, reward, scenarios).
- `train/`: Baseline training script using random actions.
- `openenv.yaml`: Environment configuration.

## Scenario: Schedule Conflict
The agent starts in an evening where both a professional meeting and a family dinner are scheduled simultaneously. The agent must decide whether to attend the meeting, attend the dinner, or attempt to balance both.

## How to Run
To run the baseline training simulation (100 episodes with random actions):

```bash
python train/train.py
```
