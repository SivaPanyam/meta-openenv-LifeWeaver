import sys
import os

# Add amals-env and backend to path
sys.path.append(os.path.join(os.getcwd(), "amals-env"))
sys.path.append(os.path.join(os.getcwd(), "backend"))

from env.environment import AMALSEnvironment
from agents.interaction import run_multi_agent
from tools.tool_manager import execute_tool

def test_tool_flow():
    print("=== TOOL LAYER VERIFICATION ===\n")
    
    # 1. Initialize Environment
    env = AMALSEnvironment()
    state = env.reset()
    
    print(">> Initial Schedule:")
    for e in state["events"]:
        print(f"   - [{e['domain'].upper()}] {e['time']}: {e['type']} ({e['priority']})")

    # 2. Force a conflict manually for testing
    print("\n>> Forcing conflict manually (setting first two events to 10:00)...")
    if len(state["events"]) >= 2:
        state["events"][0]["time"] = "10:00"
        state["events"][1]["time"] = "10:00"
    
    # Update internal state to match our manual edit
    # In a real scenario, this would be the state passed to agents
    
    # 3. Run multi-agent system
    print("\n>> Running Multi-Agent Analysis...")
    result = run_multi_agent(state)
    
    final_action = result.get("final_action", {})
    print(f"   Agent Decision: {final_action.get('action').upper()} on {final_action.get('target')}")
    print(f"   Reasoning: {result.get('reasoning')}")

    # 4. Run tool manager to apply decision
    print("\n>> Executing Tool Manager...")
    # Add a dummy new_time if reschedule is chosen (simulating backend logic)
    if final_action.get("action") == "reschedule":
        final_action["new_time"] = "14:00"

    updated_state, tool_response, tool_tag = execute_tool(final_action, state)
    
    # 5. Print updated state
    print("\n>> Updated Schedule:")
    for e in updated_state["events"]:
        status = f" [{e['status'].upper()}]" if "status" in e else ""
        print(f"   - {e['time']}: {e['type']}{status}")

    print(f"\n>> Tool Used: {tool_tag}")
    print(f">> Tool Response: {tool_response}")

    # Final Verification
    if tool_tag != "none":
        print("\n✅ FLOW VERIFIED: Agent decision successfully translated to state update.")
    else:
        print("\n❌ FLOW FAILED: No tool was executed.")

if __name__ == "__main__":
    test_tool_flow()
