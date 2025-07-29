from __future__ import annotations
import os
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from .subagents.quizmanager.agent import quiz_manager
from .subagents.commentaryagent.agent import commentaryagent

APP_NAME = "quiz-app"
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

    Possible user intents:
    1. "start_quiz" - The user wants to start a quiz.
    2. "start_commentary" - The user wants to start a financial market commentary.


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
        return {"status": "success"}
    else:
        return {"status": "error", "message": "Invalid intent"}


# define the root agent
root_agent = Agent(
    name="RootAgent",
    model=MODEL_GEMINI,
    instruction="""
    
    You are the root agent. 
    Your main role is to determine the user's intent and delegate the conversation to the appropriate subagent or keep the 
    conversation going if user doesn't need a any tailored use of the subagents.
    
    Possible intents:

    1. If the user wants to start a quiz, use your tool `state_change` with the intent `start_quiz`, and then delegate 
        to the QuizManager agent.
    2. If the user wants to start a financial market commentary, use your tool `state_change` with the intent `start_commentary`
        and then delegate to the CommentaryAgent agent.
    3. If the user wants to chat about something unrelated to the quiz or commentary, keep the converstation going with the user. 

    """,
    description="Determines the user's intent and delegates the conversation to the appropriate subagent if needed.",
    tools=[state_change],
    sub_agents=[quiz_manager, commentaryagent],
)
