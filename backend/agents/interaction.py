import sys
import os

# Add the current directory to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

try:
    from calendar_agent import calendar_agent
    from email_agent import email_agent
    from career_agent import career_agent
    from social_agent import social_agent
    from coordinator_agent import coordinator_agent
except ImportError:
    from agents.calendar_agent import calendar_agent
    from agents.email_agent import email_agent
    from agents.career_agent import career_agent
    from agents.social_agent import social_agent
    from agents.coordinator_agent import coordinator_agent

def run_multi_agent(state: dict) -> dict:
    """
    Orchestrates the multi-agent negotiation process:
    1. Collects insights from specialized advocates (Career, Social).
    2. Gathers logistical advice (Calendar, Email).
    3. Synthesizes a final decision via the Coordinator.
    """
    try:
        # Collect all agent perspectives
        calendar_output = calendar_agent(state)
        email_output = email_agent(state)
        career_output = career_agent(state)
        social_output = social_agent(state)
        
        # Aggregate outputs
        agent_outputs = [
            calendar_output, 
            email_output, 
            career_output, 
            social_output
        ]
        
        # Run coordinator for final decision
        final_result = coordinator_agent(state, agent_outputs)
        
        return {
            "agent_outputs": agent_outputs,
            "final_action": final_result["final_action"],
            "reasoning": final_result["reasoning"]
        }
        
    except Exception as e:
        return {
            "agent_outputs": [],
            "final_action": {"action": "no_change"},
            "reasoning": [f"Error in multi-agent engine: {str(e)}"]
        }
