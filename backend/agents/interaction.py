import sys
import os

# Add the current directory to sys.path to ensure absolute imports for agents work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from calendar_agent import calendar_agent
    from email_agent import email_agent
    from coordinator_agent import coordinator_agent
except ImportError:
    # Fallback for different execution contexts
    from agents.calendar_agent import calendar_agent
    from agents.email_agent import email_agent
    from agents.coordinator_agent import coordinator_agent

def run_multi_agent(state: dict) -> dict:
    """
    Orchestrates the multi-agent decision process:
    1. Collects insights from specialized agents (Calendar, Email).
    2. Synthesizes a final decision via the Coordinator.
    """
    try:
        # Step 1: Run specialized agents
        calendar_output = calendar_agent(state)
        email_output = email_agent(state)
        
        # Step 2: Aggregate outputs
        agent_outputs = [calendar_output, email_output]
        
        # Step 3: Run coordinator for final decision
        final_result = coordinator_agent(state, agent_outputs)
        
        # Step 4: Return consolidated response
        return {
            "agent_outputs": agent_outputs,
            "final_action": final_result["final_action"],
            "reasoning": final_result["reasoning"]
        }
        
    except Exception as e:
        # Error Handling Fallback
        return {
            "agent_outputs": [],
            "final_action": {"action": "no_change"},
            "reasoning": [f"Error in multi-agent engine: {str(e)}"]
        }
