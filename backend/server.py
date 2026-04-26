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
    from tools.calendar_tool import parse_event_times, format_event_time
    from explanation.explainer import generate_explanation
    from memory.memory_store import save_experience
except ImportError:
    from backend.agents.interaction import run_multi_agent
    from env.environment import AMALSEnvironment
    from backend.tools.tool_manager import execute_tool
    from backend.tools.calendar_tool import parse_event_times, format_event_time
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
        "current_date": obs.get("current_date"),
        "current_time": obs.get("current_time"),
        "full_state": obs
    }

@app.post("/tick")
async def tick(minutes: int = 30):
    new_time = env.tick(minutes)
    return {"current_time": new_time}

@app.get("/notifications")
async def get_notifications():
    """Checks for events that have ended relative to current_time."""
    state = env.state()
    events = state.get("events", [])
    current_time_str = env.current_time
    current_date_str = state["internal_truth"].current_date
    
    now_dt = datetime.strptime(f"{current_date_str} {current_time_str}", "%Y-%m-%d %H:%M")
    
    pending_notifications = []
    for event in events:
        if event.get("status") in ["completed", "skipped"]: continue
        
        start_dt, end_dt = parse_event_times(event)
        # If current time is >= end time, and it was previously 'ongoing' or 'rescheduled'
        if now_dt >= end_dt:
            pending_notifications.append({
                "type": "event_completion_check",
                "event": event["type"],
                "message": f"Did you finish '{event['type']}'?",
                "original_end": format_event_time(end_dt)
            })
            
    return {"notifications": pending_notifications}

@app.post("/respond")
async def respond(event_type: str, response: str):
    """
    Handles user interaction:
    - 'yes': Mark completed.
    - 'no': Extend duration by 30 mins.
    """
    state = env.state()
    from tools.calendar_tool import handle_event_completion
    
    updated_state, msg = handle_event_completion(state, event_type, response)
    env.events = updated_state["events"] # Persist to environment
    
    return {"status": "success", "message": msg, "events": env.events}

@app.post("/optimize")
async def optimize():
    # 1. Get Initial State
    initial_state = env.state()
    
    # 2. Run Multi-Agent Analysis
    agent_result = run_multi_agent(initial_state)
    agent_outputs = agent_result.get("agent_outputs", [])
    
    # Support Recursive Resolution (List of Actions)
    final_actions = agent_result.get("final_actions", [])
    if not final_actions:
        final_actions = [agent_result.get("final_action", {})]
    
    # 3. Execute Decision via Tool Manager
    updated_state, tool_resp, tools_used = execute_tool(final_actions, initial_state)
    
    # 4. Generate Structured Explanation
    explanation = generate_explanation(
        old_state=initial_state,
        agent_outputs=agent_outputs,
        final_actions=final_actions,
        tools_used=tools_used,
        new_state=updated_state
    )

    # 5. SAVE EXPERIENCE (Learning Phase)
    # Using the first action for simple memory storage (legacy)
    primary_decision = final_actions[0].get("action") if final_actions else "no_change"
    primary_target = final_actions[0].get("target") if final_actions else None
    
    # Extract detailed features for ML training
    prof_events = [e for e in initial_state["events"] if e["domain"] == "professional"]
    pers_events = [e for e in initial_state["events"] if e["domain"] == "personal"]
    
    prof_high = any(e for e in prof_events if e["priority"] == "high")
    pers_high = any(e for e in pers_events if e["priority"] == "high")
    
    # Feature vector for ML
    features = {
        "prof_count": len(prof_events),
        "pers_count": len(pers_events),
        "prof_high_prio": 1 if prof_high else 0,
        "pers_high_prio": 1 if pers_high else 0,
        "any_inflexible": 1 if any(not e.get("flexible") for e in initial_state["events"]) else 0,
        "conflict_detected": 1 if initial_state.get("has_conflict") else 0
    }

    state_summary = "double_high_conflict" if (prof_high and pers_high) else "prof_dominant" if prof_high else "pers_dominant" if pers_high else "balanced_conflict"

    experience = {
        "state_summary": state_summary,
        "features": features,
        "decision": primary_decision,
        "target": primary_target,
        "tools": tools_used,
        "reward": 0.9 if "calendar.reschedule" in tools_used else 0.5,
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
