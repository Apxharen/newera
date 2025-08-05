from google.adk.agents import Agent
from pydantic import BaseModel, Field
from google.adk.models.llm_response import LlmResponse
from google.adk.agents.callback_context import CallbackContext
import json
from google.genai import types

class Question(BaseModel):
     question: str = Field(description="The question to be asked")
     correct_answer: str = Field(description="The correct answer to the question")
     options: list[str] = Field(description="The options to the question")
     explanation: str = Field(description="The explanation of the correct answer")

async def load_and_inject_artifact(llm_request, callback_context: CallbackContext) -> None:
    """Load artifact and inject it directly into the LLM request in one step."""
    
    try:
        # Load the artifact
        finance_artifact = await callback_context.load_artifact(filename="summary")

        if finance_artifact and finance_artifact.inline_data:
            # For debugging - show content preview
            artifact_content = finance_artifact.inline_data.data.decode('utf-8')
            print(f"Loaded artifact: summary with {len(artifact_content)} characters")
            print(f"Content preview: {artifact_content[:200]}...")
            
            from google.genai import types
            
            # Follow the exact pattern from load_artifacts_tool.py (lines 100-110)
            artifact_message = types.Content(
                role='user',
                parts=[
                    types.Part.from_text(
                        text='Artifact summary is:'
                    ),
                    finance_artifact,  # Use the actual artifact Part object
                ],
            )
            
            # Insert the artifact content at the beginning of the conversation  
            if not llm_request.contents:
                llm_request.contents = []
            llm_request.contents.insert(0, artifact_message)
            
            print(f"Injected artifact Part object into LLM request")
        else:
            print(f"No artifact found: summary")

    except Exception as e:
        print(f"Unexpected error while loading artifact: {e}")
    except ValueError as e:
        print(f"Error loading artifact: Is Artifact Service running? {e}")

# define the callback that changes the response to the user
async def modify_response(llm_response: LlmResponse, callback_context: CallbackContext) -> LlmResponse:
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
generator = Agent(
    name="Generator",
    model="gemini-2.5-flash",
    instruction="""You are the generator. 
    Your ONLY role is to generate a question and answer for the user from the provided financial trading content.
    
    Read the ENTIRE document content provided to you and use ALL parts of it for question generation. 
    Use random sections of the document for question generation
    
    DO NOT generate questions about the file format or metadata. 
    
    You must produce the output in a following format:
    {
    "question": "text of question",
    "correct_answer": "ONLY correct answer. e.g. for multiple choice questions just correct letter of the question, e.g. a, b, c, d. For True/False either True or False. For Yes/No either Yes or No.",
    "options": ["text of options available, one after another"],
    "explanation": "text of explanation of the correct answer"
    }.
    IMPORTANT: Please remeber that options must be either True/False, Multiple Choice, or Yes/No. Decide randomly which option variant it is. 
        -  If True/False YOU MUST present them as True, False 
        -  If Multiple Choice YOU MUST present them as a), b), c), d).
        -  If Yes/No YOU MUST present them as Yes, No
    IMPORTANT: This output will be stored for other agents to use. You do not present anything to the user.
    IMPORTANT: Make sure that while generating the question you take into account the difficulty level that's passed to you from {state.difficulty}
    
    CRITICAL: AVOID REPETITION! Previously asked questions: {state.questions_asked}
    You MUST generate a question that is completely different from all the questions listed above. 
    Focus on different topics, concepts, or areas of the document that haven't been covered yet.
    If all major topics have been covered, approach them from a different angle or ask about different details.
""",
    description="Generates a question, answer, options, and explanation.",
    before_model_callback=load_and_inject_artifact,  # Load and inject artifact in one step
    output_schema=Question,
    after_model_callback=modify_response,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)