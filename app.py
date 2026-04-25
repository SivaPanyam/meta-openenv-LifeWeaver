import streamlit as st
import sys
import os
from datetime import datetime, timedelta

# Add amals-env to path to allow imports from env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "amals-env"))

from env.environment import AMALSEnvironment

# --- Styling ---
st.set_page_config(page_title="LifeWeaver Assistant", page_icon="📅", layout="centered")

# Minimal CSS for layout fixes
st.markdown("""
    <style>
    .priority-badge { 
        float: right; 
        font-size: 0.8em; 
        padding: 2px 8px; 
        border-radius: 10px; 
        background: #eee;
        color: #333;
    }
    .stMarkdown p { margin-bottom: 0px; }
    </style>
    """, unsafe_allow_html=True)

# --- Backend Logic ---
def get_initial_events():
    env = AMALSEnvironment()
    obs = env.reset()
    
    # Construct a realistic day schedule based on environment state
    events = [
        {"id": 1, "title": "Family Dinner", "time": "19:30", "priority": obs.get('dinner_priority', 'medium'), "flexible": obs.get('dinner_flexible', False)},
        {"id": 2, "title": "Project Meeting", "time": "20:00", "priority": obs.get('meeting_priority', 'high'), "flexible": False},
        {"id": 3, "title": "Gym Session", "time": "18:00", "priority": "low", "flexible": True}
    ]
    return events, obs

def run_agent(events):
    optimized = []
    reasoning = []
    prio_map = {"high": 3, "medium": 2, "low": 1}
    
    processed_events = []
    busy_slots = [] # (start, end)
    
    # Sort by priority to decide what stays fixed
    sorted_by_prio = sorted(events, key=lambda x: prio_map.get(x['priority'], 1), reverse=True)
    
    for event in sorted_by_prio:
        start = datetime.strptime(event['time'], "%H:%M")
        end = start + timedelta(hours=1)
        
        # Check overlap with already fixed slots
        conflict = any(not (end <= s or start >= e) for s, e in busy_slots)
        
        new_event = event.copy()
        if conflict:
            if event['flexible']:
                # Find next available slot
                while any(not (end <= s or start >= e) for s, e in busy_slots):
                    start += timedelta(minutes=30)
                    end = start + timedelta(hours=1)
                new_event['time'] = start.strftime("%H:%M")
                new_event['status'] = "Rescheduled"
                reasoning.append(f"✅ Moved **{event['title']}** to {new_event['time']} (Flexible).")
            else:
                new_event['status'] = "Overlapping"
                reasoning.append(f"⚠ Conflicting task **{event['title']}** kept at {event['time']} due to high priority.")
        else:
            new_event['status'] = "Confirmed"
            
        busy_slots.append((start, end))
        processed_events.append(new_event)
        
    return sorted(processed_events, key=lambda x: x['time']), reasoning

# --- UI Session State ---
if "events" not in st.session_state:
    st.session_state.events, st.session_state.obs = get_initial_events()
    st.session_state.optimized = None
    st.session_state.reasoning = []

# --- Header ---
st.title("LifeWeaver — Smart Assistant")
st.markdown("### 🤖 AI-Powered Life Optimization")

# --- Layout ---
col1, col2 = st.columns([2, 1])

with col2:
    st.write("#### Controls")
    if st.button("🔄 New Day", type="primary", use_container_width=True):
        st.session_state.events, st.session_state.obs = get_initial_events()
        st.session_state.optimized = None
        st.session_state.reasoning = []
        st.rerun()
        
    if st.button("🤖 AI Optimize", use_container_width=True):
        st.session_state.optimized, st.session_state.reasoning = run_agent(st.session_state.events)
        st.rerun()
    
    st.divider()
    st.write("**Environment Context:**")
    st.write(f"- Stress: {st.session_state.obs.get('stress', 0):.2f}")
    st.write(f"- Travel Time: {st.session_state.obs.get('travel_time', 0)}m")

with col1:
    display_list = st.session_state.optimized if st.session_state.optimized else st.session_state.events
    st.write(f"#### {'Optimized' if st.session_state.optimized else 'Current'} Schedule")

    # Conflict Check for Display
    if not st.session_state.optimized:
        times = [e['time'] for e in display_list]
        if len(times) != len(set(times)):
            st.error("🚨 **Conflict:** Overlapping tasks detected.")

    for event in display_list:
        with st.container(border=True):
            cols = st.columns([1, 4, 1])
            cols[0].write(f"**{event['time']}**")
            cols[1].write(f"**{event['title']}**")
            
            p_label = event['priority'].upper()
            cols[2].markdown(f"<span class='priority-badge'>{p_label}</span>", unsafe_allow_html=True)
            
            if 'status' in event and event['status'] != "Confirmed":
                if event['status'] == "Rescheduled":
                    st.caption(f"✨ {event['status']}")
                else:
                    st.caption(f"⚠ {event['status']}")

# --- Reasoning ---
if st.session_state.reasoning:
    st.divider()
    st.write("#### 🧠 AI Decision Reasoning")
    for r in st.session_state.reasoning:
        st.write(r)

st.divider()
st.caption("Powered by AMALS RL Environment | Streamlit Native UI")
