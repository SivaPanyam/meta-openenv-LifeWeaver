def calculate_reward(decision, state):
    """
    Calculates weighted reward based on dynamic context/priorities.
    Weights: 40% task_success, 40% balance, 20% efficiency.
    """
    priority_map = {"low": 0.3, "medium": 0.6, "high": 1.0}
    
    m_p_score = priority_map[state.meeting_priority]
    d_p_score = priority_map[state.dinner_priority]
    
    task_success = 0.0
    balance = 0.0
    efficiency = 0.0

    if decision == "attend_meeting":
        task_success = m_p_score
        balance = 0.3 if state.dinner_priority == "high" else 0.6
        efficiency = 0.9
    elif decision == "attend_dinner":
        task_success = d_p_score
        balance = 0.3 if state.meeting_priority == "high" else 0.6
        efficiency = 0.4
    elif decision == "balance_both":
        task_success = (m_p_score + d_p_score) / 2
        balance = 0.9 if state.dinner_flexible else 0.5
        efficiency = 0.7

    # Travel time penalty (context-aware)
    if state.travel_time > 40:
        efficiency = max(0, efficiency - 0.3)

    # Weighted scoring
    total_reward = (0.4 * task_success) + (0.4 * balance) + (0.2 * efficiency)
    
    info = {
        "task_success": round(task_success, 2),
        "balance": round(balance, 2),
        "efficiency": round(efficiency, 2),
        "meeting_p": state.meeting_priority,
        "dinner_p": state.dinner_priority
    }
    
    return total_reward, info
