def coordinator_agent(state, agent_outputs):
    """
    Synthesizes outputs from all specialized agents to determine the final system action.
    agent_outputs: List containing [calendar_output, email_output]
    """
    # Extract specific outputs
    calendar_out = next((o for e in agent_outputs if (o := e) and o['agent'] == 'calendar_agent'), None)
    email_out = next((o for e in agent_outputs if (o := e) and o['agent'] == 'email_agent'), None)
    
    reasoning = [o["reason"] for o in agent_outputs if "reason" in o]
    
    # Decision Logic: If calendar suggests a reschedule, that is our primary resolution
    if calendar_out and calendar_out.get("action") == "reschedule":
        final_action = {
            "action": "reschedule",
            "target": calendar_out.get("target_event"),
            "notify": email_out.get("action") == "send_email" if email_out else False,
            "description": f"The system will reschedule '{calendar_out.get('target_event')}' and notify relevant parties."
        }
    else:
        final_action = {
            "action": "no_change",
            "description": "No immediate schedule adjustments are required."
        }
        
    return {
        "final_action": final_action,
        "reasoning": reasoning
    }
