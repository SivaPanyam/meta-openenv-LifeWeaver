import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# Add amals-env to path to allow imports from env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "amals-env"))

from env.environment import AMALSEnvironment

# --- Styling ---
st.set_page_config(page_title="LifeWeaver Assistant", page_icon="📅", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #007bff; color: white; }
    .event-card { padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #007bff; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .event-conflict { border-left: 5px solid #dc3545; background: #fff5f5; }
    .event-resolved { border-left: 5px solid #28a745; background: #f8fff9; }
    .priority-high { color: #dc3545; font-weight: bold; }
    .priority-medium { color: #fd7e14; font-weight: bold; }
    .priority-low { color: #6c757d; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- Backend Logic ---
def get_initial_events():
    env = AMALSEnvironment()
    obs = env.reset()
    
    # Construct a realistic day schedule based on environment state
    events = [
        {"id": 1, "title": "Family Dinner", "time": "19:30", "priority": obs['dinner_priority'], "flexible": obs['dinner_flexible']},
        {"id": 2, "title": "Project Meeting", "time": "20:00", "priority": obs['meeting_priority'], "flexible": False},
        {"id": 3, "title": "Gym Session", "time": "18:00", "priority": "low", "flexible": True}
    ]
    return events, obs

def run_agent(events):
    optimized = []
    reasoning = []
    
    # Sort by priority for decision making
    prio_map = {"high": 3, "medium": 2, "low": 1}
    sorted_events = sorted(events, key=lambda x: prio_map[x['priority']], reverse=True)
    
    busy_until = None
    
    # Pre-sort by original time for processing
    events_chronological = sorted(events, key=lambda x: x['time'])
    
    # Simplified optimization:
    # 1. Keep non-flexible High Priority events fixed.
    # 2. Shift others if they conflict.
    
    processed_events = []
    busy_slots = [] # (start, end)
    
    # First pass: High priority fixed
    for event in sorted(events, key=lambda x: prio_map[x['priority']], reverse=True):
        start = datetime.strptime(event['time'], "%H:%M")
        end = start + timedelta(hours=1)
        
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
                reasoning.append(f"Moved '{event['title']}' to {new_event['time']} to resolve conflict.")
            else:
                new_event['status'] = "Conflict Kept"
                reasoning.append(f"Retained overlap for '{event['title']}' due to {event['priority']} priority.")
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
st.title("LifeWeaver — Smart Calendar Agent")
st.markdown("##### AI-powered schedule optimization")

# --- Layout ---
col1, col2 = st.columns([2, 1])

with col2:
    st.write("### Controls")
    if st.button("🔄 Refresh Schedule"):
        st.session_state.events, st.session_state.obs = get_initial_events()
        st.session_state.optimized = None
        st.session_state.reasoning = []
        st.rerun()
        
    if st.button("🤖 Optimize Schedule", type="primary"):
        st.session_state.optimized, st.session_state.reasoning = run_agent(st.session_state.events)
        st.rerun()

    show_reasoning = st.toggle("Show Agent Decisions", value=True)

with col1:
    display_list = st.session_state.optimized if st.session_state.optimized else st.session_state.events
    
    st.write(f"### {'Optimized' if st.session_state.optimized else 'Current'} Day View")
    
    # Check for conflicts in current view (simple O(n^2) for 3 events)
    has_conflict = False
    if not st.session_state.optimized:
        for i, e1 in enumerate(display_list):
            for j, e2 in enumerate(display_list):
                if i != j and e1['time'] == e2['time']:
                    has_conflict = True
        if has_conflict:
            st.error("⚠️ Conflict detected in schedule")

    for event in display_list:
        p_class = f"priority-{event['priority']}"
        status_tag = f" — <i>{event['status']}</i>" if 'status' in event else ""
        card_class = "event-card"
        
        # Visual cues for state
        if not st.session_state.optimized and has_conflict and event['time'] in ["19:30", "20:00"]:
            card_class += " event-conflict"
        elif st.session_state.optimized:
            card_class += " event-resolved"
            
        st.markdown(f"""
            <div class="{card_class}">
                <span style="float:right;" class="{p_class}">{event['priority'].upper()}</span>
                <strong>{event['time']}</strong> | {event['title']}{status_tag}
            </div>
        """, unsafe_allow_html=True)

# --- Reasoning Panel ---
if show_reasoning and st.session_state.reasoning:
    st.divider()
    st.write("### 🤖 Why this plan?")
    for r in st.session_state.reasoning:
        st.markdown(f"- {r}")

st.divider()
st.caption("Powered by AMALS (Adaptive Multi-Agent Life Simulator) RL Environment")
