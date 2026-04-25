# GEMINI.md - AMALS (Adaptive Multi-Agent Life Simulator)

This document provides context and instructions for AI agents working on the AMALS project.

## Project Overview

AMALS is a minimal, correct OpenEnv-compatible training environment designed to simulate real-life decision-making scenarios, specifically focused on handling schedule conflicts (e.g., Meeting vs. Family Dinner). It is designed to train agents to reason about trade-offs, priorities, and efficiency.

### Key Technologies
- **Language:** Python 3
- **Standards:** OpenEnv (reset, step, state interface)
- **Dependencies:** Matplotlib (for visualization), PyYAML (for configuration)
- **Integration:** Simulated MCP (Model Context Protocol) tools for calendar management.

### Architecture
- `env/`: Core environment implementation.
    - `environment.py`: Main `AMALSEnvironment` class.
    - `reward.py`: Weighted reward logic (40% task success, 40% balance, 20% efficiency).
    - `scenarios.py`: Dynamic, context-aware scenario generation.
    - `world.py`: Data structures for environment state.
- `mcp/`: Simulated tools.
    - `calendar_server.py`: Local Calendar MCP server for scheduling and conflict detection.
- `train/`: Training and baseline scripts.
    - `train.py`: Comprehensive training script with exploration/exploitation strategy and validation suite.
- `openenv.yaml`: Environment specification for standard runners.
- `test_env.py`: Validation suite for environment correctness and OpenEnv compatibility.

## Building and Running

### Prerequisites
Install dependencies:
```bash
pip install -r amals-env/requirements.txt
```

### Verification
Run the environment validation suite to ensure compatibility and stability:
```bash
python amals-env/test_env.py
```

### Training
Run the baseline training script with learning validation and reward plotting:
```bash
python amals-env/train/train.py
```

## Development Conventions

### Environment Interface
Any environment extension or replacement must adhere to the OpenEnv standard:
- `reset()`: Returns initial state.
- `state()`: Returns current observation dict.
- `step(action)`: Returns `(state, reward, done, info)`.

### Action Format
Actions are passed as dictionaries:
```json
{"decision": "attend_meeting" | "attend_dinner" | "balance_both"}
```

### Reward Philosophy
Rewards are **non-binary** and **context-dependent**. They are computed based on:
1. **Task Success:** Scaled by the priority (low/medium/high) of the chosen task.
2. **Balance:** Penalized if high-priority tasks are missed.
3. **Efficiency:** Penalized for high travel times (> 40 mins).

### Tool Integration
Actions should be "executed" through the simulated MCP servers in `mcp/`. Tool outputs must be returned in the `info` dictionary of the `step` method.
