import streamlit as st
import sys
import os
import random

# Add amals-env to path to allow imports from env and mcp_local
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "amals-env"))

from env.environment import AMALSEnvironment

# --- Page Config ---
st.set_page_config(page_title="LifeWeaver Simulator", page_icon="🧬", layout="centered")

# --- Initialize Environment ---
if "env" not in st.session_state:
    st.session_state.env = AMALSEnvironment()
    st.session_state.obs = st.session_state.env.reset()
    st.session_state.total_reward = 0
    st.session_state.history = []

def reset_game():
    st.session_state.obs = st.session_state.env.reset()
    st.session_state.total_reward = 0
    st.session_state.history = []
    st.rerun()

# --- Header ---
st.title("🧬 LifeWeaver: Decision Calendar Simulator")
st.markdown("Training agents to weave a balanced life through sequential decision making.")

# --- Sidebar Context ---
with st.sidebar:
    st.header("📊 Current Context")
    obs = st.session_state.obs
    st.metric("Stress Level", f"{obs.get('stress', 0.0):.2f}")
    st.metric("Travel Time", f"{obs.get('travel_time', 0)} mins")
    
    st.subheader("🎯 Priorities")
    m_p = obs.get('meeting_priority', 'low').upper()
    d_p = obs.get('dinner_priority', 'low').upper()
    st.write(f"**Meeting:** {m_p}")
    st.write(f"**Dinner:** {d_p}")
    
    st.divider()
    if st.button("Start New Scenario", type="primary", use_container_width=True):
        reset_game()

# --- Calendar Display ---
st.subheader("📅 Today's Schedule")
cal_col1, cal_col2 = st.columns(2)

with cal_col1:
    st.info("🕒 **7:30 PM**\n\nFamily Dinner")
with cal_col2:
    st.info("🕒 **8:00 PM**\n\nProfessional Meeting")

st.warning("⚠️ **Conflict Detected:** Overlapping commitments at 8:00 PM.")

# --- Game Flow ---
step = obs.get("step", 0)

# STEP 0: PLANNING
if step == 0:
    st.subheader("📝 Phase 1: Planning")
    st.write("How do you intend to handle this conflict?")
    
    col1, col2, col3 = st.columns(3)
    if col1.button("Attend Meeting", use_container_width=True):
        _, r, _, _ = st.session_state.env.step({"decision": "attend_meeting"})
        st.session_state.total_reward += r
        st.session_state.obs = st.session_state.env.get_observation()
        st.rerun()
    if col2.button("Attend Dinner", use_container_width=True):
        _, r, _, _ = st.session_state.env.step({"decision": "attend_dinner"})
        st.session_state.total_reward += r
        st.session_state.obs = st.session_state.env.get_observation()
        st.rerun()
    if col3.button("Balance Both", use_container_width=True):
        _, r, _, _ = st.session_state.env.step({"decision": "balance_both"})
        st.session_state.total_reward += r
        st.session_state.obs = st.session_state.env.get_observation()
        st.rerun()

# STEP 1: EXECUTION
elif step == 1:
    st.subheader("⚡ Phase 2: Execution")
    plan = obs.get("last_decision", "None").replace("_", " ").title()
    st.write(f"Your plan is set to: **{plan}**")
    st.write("Uncertainty is at play. External factors like stress and travel may impact the outcome.")
    
    if st.button("Execute Schedule", type="primary", use_container_width=True):
        _, r, _, _ = st.session_state.env.step({"decision": obs.get("last_decision")})
        st.session_state.total_reward += r
        st.session_state.obs = st.session_state.env.get_observation()
        st.rerun()

# STEP 2: RECOVERY
elif step == 2:
    st.subheader("🔧 Phase 3: Recovery")
    outcome = obs.get("outcome")
    
    if outcome == "success":
        st.success("✅ **Outcome: Success**")
        st.write("The plan worked perfectly!")
    elif outcome == "partial":
        st.warning("⚠️ **Outcome: Partial Success**")
        st.write("You managed some tasks, but others were delayed or missed.")
    else:
        st.error("❌ **Outcome: Failure**")
        st.write("The schedule collapsed due to external pressures.")
        if obs.get("stress") > 0.6:
            st.caption("Reason: High stress significantly reduced your success probability.")

    st.write("Choose a recovery action to mitigate the impact:")
    rec_col1, rec_col2, rec_col3, rec_col4 = st.columns(4)
    
    if rec_col1.button("Reschedule", use_container_width=True):
        _, r, _, _ = st.session_state.env.step({"decision": "reschedule_meeting"})
        st.session_state.total_reward += r
        st.session_state.obs = st.session_state.env.get_observation()
        st.rerun()
    if rec_col2.button("Delay Dinner", use_container_width=True):
        _, r, _, _ = st.session_state.env.step({"decision": "delay_dinner"})
        st.session_state.total_reward += r
        st.session_state.obs = st.session_state.env.get_observation()
        st.rerun()
    if rec_col3.button("Apologize", use_container_width=True):
        _, r, _, _ = st.session_state.env.step({"decision": "send_apology_email"})
        st.session_state.total_reward += r
        st.session_state.obs = st.session_state.env.get_observation()
        st.rerun()
    if rec_col4.button("Do Nothing", use_container_width=True):
        _, r, _, _ = st.session_state.env.step({"decision": "none"})
        st.session_state.total_reward += r
        st.session_state.obs = st.session_state.env.get_observation()
        st.rerun()

# STEP 3: FINAL
else:
    st.subheader("🏁 Final Result")
    reward = st.session_state.total_reward
    st.metric("Total Cumulative Reward", f"{reward:.2f}")
    
    if reward > 1.2:
        st.balloons()
        st.success("Master Weaver! You handled the conflict and recovery effectively.")
    elif reward > 0.8:
        st.info("Good effort. You maintained balance despite the challenges.")
    else:
        st.warning("Room for improvement. The simulation highlights the cost of poor planning or lack of recovery.")

    if st.button("Try Another Scenario", use_container_width=True):
        reset_game()

# --- Footer ---
st.divider()
st.caption("LifeWeaver 🧬 - An OpenEnv Compatible RL Training Environment")
