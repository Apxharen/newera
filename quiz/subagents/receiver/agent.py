from google.adk.agents import Agent
from google.adk.tools import ToolContext


#TOOLS

def get_user_input(tool_context: ToolContext) -> str:

    """ Get's user input from user"""

    user_input = input("Your answer?: ")

    session_state = tool_context.state
    session_state["user_input"] = user_input
    
    return {"status: success"}

#AGENTS
receiver = Agent(
    name="receiver",
    instruction="""
    You are receiver agent. Your only job when you're called is to get user input via your
    get_user_input tool.
    """,
    tools=[get_user_input],
)