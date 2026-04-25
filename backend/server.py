from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import random
from datetime import datetime, timedelta

# Add amals-env to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "amals-env"))

from env.environment import AMALSEnvironment

app = FastAPI()

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global environment instance
env = AMALSEnvironment()

@app.get("/reset")
async def reset():
    obs = env.reset()
    return {
        "events": obs.get("events", []),
        "stress": obs.get("stress", 0),
        "travel_time": obs.get("travel_time", 0)
    }

@app.post("/optimize")
async def optimize(data: dict):
    events = data.get("events", [])
    prio_map = {"high": 3, "medium": 2, "low": 1}
    
    # Simple heuristic optimization logic
    # 1. Sort by priority
    # 2. Assign slots without overlap
    sorted_events = sorted(events, key=lambda x: prio_map.get(x['priority'], 1), reverse=True)
    
    optimized = []
    busy_slots = []
    
    for event in sorted_events:
        new_event = event.copy()
        time_str = event['time'].replace(" PM", "").replace(" AM", "")
        try:
            # Handle formats like "18:00" or "6:00"
            start = datetime.strptime(time_str, "%H:%M") if ":" in time_str else datetime.strptime(time_str, "%H")
        except:
            start = datetime.strptime("18:00", "%H:%M")
            
        end = start + timedelta(minutes=event.get('duration', 60))
        
        # Check overlap
        conflict = any(not (end <= s or start >= e) for s, e in busy_slots)
        
        if conflict and event.get('flexible'):
            # Find next free slot
            while any(not (end <= s or start >= e) for s, e in busy_slots):
                start += timedelta(minutes=30)
                end = start + timedelta(minutes=event.get('duration', 60))
            new_event['time'] = start.strftime("%I:%M %p")
            new_event['status'] = "rescheduled"
        elif conflict:
            new_event['status'] = "conflict"
        else:
            new_event['status'] = "fixed"
            
        busy_slots.append((start, end))
        optimized.append(new_event)
        
    return {"events": sorted(optimized, key=lambda x: x['time'])}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
