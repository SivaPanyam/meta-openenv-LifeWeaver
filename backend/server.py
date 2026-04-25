from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
from datetime import datetime, timedelta

# Ensure absolute paths for imports regardless of where uvicorn is started
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, "backend"))
sys.path.append(os.path.join(BASE_DIR, "amals-env"))

try:
    from agents.interaction import run_multi_agent
    from env.environment import AMALSEnvironment
except ImportError:
    # Fallback for alternative path configurations
    from backend.agents.interaction import run_multi_agent
    from env.environment import AMALSEnvironment

app = FastAPI()

# 7. Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 6. Initialize Environment
env = AMALSEnvironment()

# 3. Root endpoint to prevent "Not Found"
@app.get("/")
def root():
    return {"message": "LifeWeaver Backend is running", "status": "online"}

# 4. Endpoints
@app.get("/reset")
async def reset():
    print(">> Resetting environment...")
    obs = env.reset()
    # Ensure events is always a list
    events = obs.get("events", [])
    return {
        "events": events,
        "full_state": obs
    }

@app.post("/optimize")
async def optimize():
    print(">> Running Multi-Agent Optimization...")
    current_state = env.state()
    events = current_state.get("events", [])
    
    result = run_multi_agent(current_state)
    
    final_decision = result.get("final_action", {})
    action_type = final_decision.get("action")
    target_type = final_decision.get("target")
    
    updated_events = [e.copy() for e in events]
    
    if action_type == "reschedule" and target_type:
        for event in updated_events:
            if event["type"] == target_type:
                time_str = event["time"].replace(" PM", "")
                try:
                    hour = int(time_str.split(":")[0])
                    new_hour = (hour % 12) + 1
                    event["time"] = f"{new_hour}:00 PM"
                    event["status"] = "rescheduled"
                except:
                    event["time"] = "10:00 PM"
                    event["status"] = "rescheduled"

    return {
        "events": updated_events,
        "agent_outputs": result.get("agent_outputs", []),
        "reasoning": result.get("reasoning", [])
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
