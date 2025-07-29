from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.callback_context import CallbackContext
from pydantic import BaseModel, Field
from google.adk.models.llm_response import LlmResponse
from google.genai import types

import os
import json

#OUTPUT SCHEMAS
class OraclerResponse(BaseModel):
    outcome: str = Field(description="The outcome of the user's answer")
    determined_difficulty: str = Field(description="The new difficulty level")
    difficulty_text: str = Field(description="Slightly longer text explainling the difficulty level'")



#CALLBACKS
def mission_critical(llm_response: LlmResponse, callback_context: CallbackContext) -> LlmResponse:
    """Saves the current question, user answer and correct answer to the session state.
    Increments the number of questions answered.
    Saves the user answer for a given question to the session state.
    Saves the determined difficulty to the session state if it was changed. 
    """
    full_response_text = llm_response.content.parts[0].text
    full_response_data = json.loads(full_response_text)

    print(full_response_data)

    session_state = callback_context.state
    
    outcome = full_response_data.get("outcome", "")
    determined_difficulty = full_response_data.get("determined_difficulty", "")

    # Update session state based on outcome
    if outcome == "correct":
        callback_context.state["points_scored"] += 1
    
    # Always append the outcome to answers list
    callback_context.state["answers"] = callback_context.state["answers"] + [outcome]
    
    # Update difficulty in session state if it changed
    if determined_difficulty != callback_context.state["difficulty"]:
        callback_context.state["difficulty"] = determined_difficulty

    # Increment the number of questions answered
    callback_context.state["no_q_answered"] += 1
    
    # Store the full response data for QuizManager to use
    callback_context.state["current_outcome"] = full_response_data
    
    # IMPORTANT: Don't modify the response content - keep the original JSON
    # The QuizManager tool expects structured output, but we can create a user-friendly
    # display message separately if needed
    
    print(f"Updated session state - Score: {callback_context.state['points_scored']}, Answers: {callback_context.state['answers']}")
    
    return llm_response


#AGENTS
oracler = Agent(
    name="Oracler",
    model="gemini-2.5-flash",
    instruction="""You are the Oracler. 
    Your ONLY role is evaluate the user's answer to the question, check if it is correct or incorrect, provide the explanation if incorrect and 
    determine the new difficulty level. 

    State variables:
    * {state.current_question}: The current question object:
        - {state.current_question.correct_answer}: The correct answer to the question.
        - {state.current_question.explanation}: The explanation of the correct answer.
        - {state.current_question.question}: The question itself.
        - {state.current_question.options}: The options to the question.
    * {state.answers}: A list of the user's answer outcomes ('correct', 'incorrect').
    * {state.difficulty}: The current difficulty level ('easy', 'medium', 'hard').
    * {state.points_scored}: The user's current score.
    * {state.no_q_answered}: The total number of questions the user has answered.
    * {state.q_state}: A boolean indicating if the quiz is active.

    Evaluation steps:
    
    ** Step 1. Check if user answered correctly:** 
        CRITICAL: The correct answer is stored EXACTLY in `{state.current_question.correct_answer}`.
        
        Follow this EXACT comparison logic:
        
        1. Extract the user's answer choice letter:
           - If user answered e.g. "a)", "b)", "c)", or "d)" → extract just the letter (a, b, c, d)
           - If user answered e.g. "A)", "B)", "C)", or "D)" → extract just the letter and convert to lowercase (a, b, c, d)
           - If user answered just "a", "b", "c", "d" → use as is
           - If user answered just "A", "B", "C", "D" → convert to lowercase (a, b, c, d)
        
        2. Extract the correct answer choice letter:
           - From `{state.current_question.correct_answer}`, extract the choice letter using the same logic as above
        
        3. Compare the letters:
           - If the extracted letters match EXACTLY → answer is CORRECT
           - If the extracted letters do NOT match → answer is INCORRECT
        
        4. For True/False questions:
           - User answers "true", "t", "True", "T" → compare against correct answer
           - User answers "false", "f", "False", "F" → compare against correct answer
        
        5. For Yes/No questions:
           - User answers "yes", "y", "Yes", "Y" → compare against correct answer
           - User answers "no", "n", "No", "N" → compare against correct answer

    ** Step 2. Determine Difficulty:**
        * Check for a streak of **two correct answers**: If the user's current answer is 'correct' and the last entry in `{state.answers}` was also 'correct', increase the difficulty by one level (e.g., 'easy' → 'medium'). The new difficulty cannot exceed 'hard'.
        * Check for a streak of **two incorrect answers**: If the user's current answer is 'incorrect' and the last entry in `{state.answers}` was also 'incorrect', decrease the difficulty by one level (e.g., 'hard' → 'medium'). The new difficulty cannot go below 'easy'.
        * If the difficulty changed, inform the user (e.g., "Let's try something a bit harder."), but if the difficulty is not changed, do not inform the user (e.g -> if the `determined_difficulty` is equal to `{state.difficulty}`, do not inform the user).

        You must produce the output in a following format:
        {
            "outcome": "only 'correct' or 'incorrect'",
            "determined_difficulty": "the new difficulty level - only 'easy', 'medium', 'hard'",
            "difficulty_text": "slightly longer text explainling the difficulty level, e.g. for 'easy' 'Let's try something a bit easier', for 'medium' 'Let's try something a bit harder', for 'hard' 'Let's try something a bit harder'"
        }

    Critical constraints:
    * If for any reason you determine {state.q_state} is False, you Must return control to the QuizManager agent.
    * Immediately after producing the output, send back control to the QuizManager agent.
    """,
    description="Evaluates the user's answer to the question, checks if it is correct or incorrect, provides the explanation if incorrect and determines the new difficulty level.",
    output_schema=OraclerResponse,
    after_model_callback=[mission_critical],
)

