from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from pydantic import BaseModel, Field
from google.adk.models.llm_response import LlmResponse
import json
from google.genai import types

class Question(BaseModel):
     question: str = Field(description="The question to be asked")
     correct_answer: str = Field(description="The correct answer to the question")
     options: list[str] = Field(description="The options to the question")
     explanation: str = Field(description="The explanation of the correct answer")

#CALLBACKS

async def load_artifacts(callback_context: CallbackContext) -> None:
    """Loads the artifacts from the artifact service."""

    text = "finance"

    try:
        finance_artifact = await callback_context.load_artifact(filename=text)

        if finance_artifact and finance_artifact.inline_data:
            print(f"Loaded artifact: {text}")
        else:
            print(f"No artifact found: {text}")

    except Exception as e:
        print(f"Unexpected error while loading artifact: {e}")
    except ValueError as e:
        print(f"Error loading artifact: Is Artifact Service running? {e}")
    
    callback_context.state["artifact"] = True

    return None

# define the callback that changes the response to the user
def modify_response(llm_response: LlmResponse, callback_context: CallbackContext) -> LlmResponse:
    """After the model has generated a response, we need to parse the response and store it in the state."""
    full_response_text = llm_response.content.parts[0].text
    full_response_data = json.loads(full_response_text)

    session_state = callback_context.state
    session_state["current_question"] = full_response_data
    session_state["questions_asked"] = session_state["questions_asked"] + [full_response_data]
    session_state["no_q_asked"] += 1

    question = full_response_data.get("question", "")
    options = full_response_data.get("options", [])
    
    formatted_options = "\n".join(f"- {option}" for option in options)
    user_message = f"Question: {question}\n\nOptions:\n{formatted_options}"

    new_content = types.Content(
        parts=[types.Part(text=user_message)],
        role="model"
    )
    llm_response.content = new_content
    return llm_response

# define the question generator agent
question_generator = Agent(
    name="QuestionGenerator",
    model="gemini-2.5-flash",
    instruction="""You are the question generator. 
    Your ONLY role is to generate a question and answer for the user from the artifact `finance`. 
    You must produce the output in a following format:
    {
    "question": "text of question",
    "correct_answer": "text of correct answer",
    "options": ["text of options available, one after another"],
    "explanation": "text of explanation of the correct answer"
    }.
    IMPORTANT: Please remeber that options must be either: True/False, Multiple Choice, or Yes/No. If multiple choice, present them as a), b), c), d).
    This output will be stored for other agents to use. You do not present anything to the user.
   Make sure that while generating the question you take into account the difficulty level that's passed to you from {state.difficulty}

   IMPORTANT:After producing the output, send back control to the QuizManager agent.""",
    description="Generates a question, answer, options, and explanation.",
    before_agent_callback=load_artifacts,
    output_schema=Question,
    after_model_callback=modify_response,
)