from __future__ import annotations
import os
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from .modes.quiz.agent import quiz_manager
from .modes.commentary.agent import commenter_agent
from .modes.sql_forge.agent import sql_forge_manager

APP_NAME = "vresc-app"
USER_ID = "user1" 
SESSION_ID = "session1"
MODEL_GEMINI = "gemini-2.5-flash"


#TOOLS
#define the state_change tool
async def state_change(user_intent: str,tool_context: ToolContext) -> str:
    """
    Changes the state of the conversation to the appropriate state based on the user's intent, and loads the necessary session state.

    Possible different states:
    1. "Quiz" - The user wants to start a quiz.
    2. "Commentary" - The user wants to start a financial market commentary.
    3. "SQL Forge" - The user wants to generate BigQuery SQL.

    Possible user intents:
    1. "start_quiz" - The user wants to start a quiz.
    2. "start_commentary" - The user wants to start a financial market commentary.
    3. "start_sql_forge" - The user wants to generate BigQuery SQL.


    """
    if user_intent == "start_quiz":
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Load summary.txt and save it as an artifact
        summary_path = os.path.join(script_dir, "data", "summary.txt")
        with open(summary_path, "rb") as f:
            summary_bytes = f.read()
        summary_part = types.Part.from_bytes(data=summary_bytes, mime_type="text/plain")
        await tool_context.save_artifact(filename="summary", artifact=summary_part)

        # Load full_text.txt and save it as an artifact
        full_text_path = os.path.join(script_dir, "data", "finance.pdf")
        with open(full_text_path, "rb") as f:
            full_text_bytes = f.read()
        full_text_part = types.Part.from_bytes(
            data=full_text_bytes, mime_type="application/pdf"
        )
        await tool_context.save_artifact(filename="finance", artifact=full_text_part)

        tool_context.state["q_state"] = True
        tool_context.state["no_q_asked"] = 0
        tool_context.state["no_q_answered"] = 0
        tool_context.state["current_question"] = None
        tool_context.state["points_scored"] = 0
        tool_context.state["answers"] = []
        tool_context.state["questions_asked"] = []
        tool_context.state["difficulty"] = "medium"
        return {"status": "success"}
    elif user_intent == "start_commentary":
        tool_context.state["commmentary_state"] = True
        tool_context.state["finance_markets_data"] = None
        tool_context.state["news_summary_data"] = None
        return {"status": "success"}
    elif user_intent == "start_sql_forge":
        tool_context.state["sql_forge_state"] = True
        tool_context.state["current_database"] = None
        tool_context.state["schema_loaded"] = False
        tool_context.state["generated_sql"] = None
        tool_context.state["sql_critique"] = None
        tool_context.state["last_validation_result"] = None
        return {"status": "success"}
    else:
        return {"status": "error", "message": "Invalid intent"}


# define the root agent
root_agent = Agent(
    name="rootagent",
    model=MODEL_GEMINI,
    instruction="""
    
    You are the RootAgent - the central brain and orchestration core of the Vresc Financial Intelligence System.
    As the cognitive center of Vresc, you analyze user intent and coordinate sophisticated financial capabilities through advanced subagent delegation.
    
    Core Intelligence Capabilities:

    1. Financial Knowledge Assessment: When users seek quiz-based learning or knowledge testing, activate your `state_change` tool 
        with intent `start_quiz`, then immediately call `transfer_to_agent` with agent_name `QuizManager`.
    2. Market Intelligence Analysis: For financial market commentary, real-time insights, or market analysis requests, 
        use `state_change` with intent `start_commentary`, then immediately call `transfer_to_agent` with agent_name `CommenterAgent`.
    3. BigQuery SQL Forge: For SQL generation, database queries, or BigQuery development requests, activate your `state_change` tool
        with intent `start_sql_forge`, then immediately call `transfer_to_agent` with agent_name `SqlForgeManager`.
    4. Elite Financial Discourse: For general financial discussions, trading strategies, or investment insights, 
        engage directly with your comprehensive financial expertise and authoritative market knowledge.

    Your responses should reflect the sophistication and precision expected from the Vresc elite financial intelligence platform.
    You are the strategic mind behind Vresc's capabilities.

    """,
    description="The central brain of the Vresc Financial Intelligence System - orchestrates sophisticated market analysis and knowledge assessment capabilities.",
    tools=[state_change],
    sub_agents=[quiz_manager, commenter_agent, sql_forge_manager],
)
