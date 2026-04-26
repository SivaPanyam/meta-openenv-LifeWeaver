from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
from datetime import datetime, timedelta

# Ensure paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, "backend"))
sys.path.append(os.path.join(BASE_DIR, "amals-env"))

try:
    from agents.interaction import run_multi_agent
    from env.environment import AMALSEnvironment
    from tools.tool_manager import execute_tool
    from explanation.explainer import generate_explanation
    from memory.memory_store import save_experience
except ImportError:
    from backend.agents.interaction import run_multi_agent
    from env.environment import AMALSEnvironment
    from backend.tools.tool_manager import execute_tool
    from backend.explanation.explainer import generate_explanation
    from backend.memory.memory_store import save_experience

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

env = AMALSEnvironment()

@app.get("/")
def root():
    return {"message": "LifeWeaver Backend is running", "status": "online"}

@app.get("/reset")
async def reset():
    obs = env.reset()
    return {
        "events": obs.get("events", []),
        "full_state": obs
    }

@app.post("/optimize")
async def optimize():
    # 1. Get Initial State
    initial_state = env.state()
    
    # 2. Run Multi-Agent Analysis
    agent_result = run_multi_agent(initial_state)
    agent_outputs = agent_result.get("agent_outputs", [])
    final_decision = agent_result.get("final_action", {})
    
    # 3. Execute Decision via Tool Manager
    updated_state, tool_resp, tools_used = execute_tool(final_decision, initial_state)
    
    # 4. Generate Structured Explanation
    explanation = generate_explanation(
        old_state=initial_state,
        agent_outputs=agent_outputs,
        final_action=final_decision,
        tools_used=tools_used,
        new_state=updated_state
    )

    # 5. SAVE EXPERIENCE (Learning Phase)
    # We summarize the state and store the decision + outcome for future coordination
    prof_high = any(e for e in initial_state["events"] if e["domain"] == "professional" and e["priority"] == "high")
    pers_high = any(e for e in initial_state["events"] if e["domain"] == "personal" and e["priority"] == "high")
    state_summary = "double_high_conflict" if (prof_high and pers_high) else "prof_dominant" if prof_high else "pers_dominant" if pers_high else "balanced_conflict"

    experience = {
        "state_summary": state_summary,
        "decision": final_decision.get("action"),
        "target": final_decision.get("target"),
        "tools": tools_used,
        "reward": 0.9 if "calendar.reschedule" in tools_used else 0.5, # Simplified reward for learning
        "timestamp": str(datetime.now())
    }
    save_experience(experience)

    return {
        "events": updated_state.get("events", []),
        "explanation": explanation
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
