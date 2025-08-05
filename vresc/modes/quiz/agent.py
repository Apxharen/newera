from __future__ import annotations
from google.adk.agents import Agent

from google.adk.tools.tool_context import ToolContext
import os
from .subagents.generator.agent import generator
from .subagents.summariser.agent import summariser



#CALLBACKS

#TOOLS
async def oracler_tool(user_answer: str, correct_answer: str, tool_context: ToolContext) -> str:
    """
    Compares user answer to correct answer and checks if user got it correct.
    """

    session_state = tool_context.state

    #write everything to sessions state
    session_state["no_q_answered"] += 1
    if user_answer.lower() == correct_answer.lower():
        outcome = "correct"
        session_state["answers"] = session_state["answers"] + [outcome]
        session_state["points_scored"] += 1
        session_state["current_outcome"] = outcome

    else:
        session_state["answers"] = session_state["answers"] + ["incorrect"]
        outcome = "incorrect"
        session_state["current_outcome"] = outcome 

    # determine new difficulty
    difficulty_change = None
    difficulties = ["easy", "medium", "hard"]
    current_difficulty = session_state.get("difficulty", "")

    if len(session_state.get("answers", [])) >= 2:
        last_two_answers = session_state["answers"][-2:]
    
        # Find the numeric position (index) of the current difficulty
        current_index = difficulties.index(current_difficulty)
        new_index = current_index

        # Determine the direction of change
        if last_two_answers == ["correct", "correct"]:
                new_index += 1
                difficulty_change = "higher"
        elif last_two_answers == ["incorrect", "incorrect"]:
                new_index -= 1
                difficulty_change = "lower"

        # Clamp the index to stay within the bounds of the list [0, 2]
        # This prevents the index from going out of range.
        clamped_index = max(0, min(new_index, len(difficulties) - 1))

        # If the index has actually changed, update the state
        if clamped_index != current_index:
                session_state["difficulty"] = difficulties[clamped_index]
                return {"status": f"success, outcome is {outcome}, difficulty_change: {difficulty_change}"}
        else:
                # If no change occurred (e.g., trying to go past "hard"), reset the flag
                difficulty_change = None
                return {"status": f"success,outcome is {outcome}, difficulty_change: {difficulty_change}"}

    return {"status": f"success, outcome is {outcome}, difficulty_change: {difficulty_change}"}   
        

quiz_manager = Agent(
    name="QuizManager",
    model="gemini-2.5-pro",
    instruction="""    
            1. Persona & Core Objective

            You are the Quiz Manager. Your job is to orchestrate a quiz, by following predefined rules and use your subagents or tools to achieve it. 


            2. Quiz Logic Flow

            Your Action Rules:

            Your action is determined by the most recent event in the quiz. 
            Rule number 1 is the most important one.
            Rule number 2 is the second most important one.
            Rule number 3 is the third most important one.
            Rule number 4 is the fourth most important one.
            Rule number 5 is the fifth most important one.

            RULE 1: If the quiz state ({state.q_state}) is False:
                Your action is to transfer control to the RootAgent.

            RULE 2: If the number of answered questions ({state.no_q_answered}) is 9:
                Extract the response from {state.current_outcome} and:
                    - if outcome is "correct": inform user about it saying e.g. "Correct! You got it right!" or "Nice, that's the correct answer!"
                    - if outcome is "incorrect": inform user about it saying e.g. "Incorrect! The correct answer is {state.current_question.correct_answer}." and provide the explanation from {state.current_question.explanation}, so the user can learn.
                - Then immediately proceed to call summariser agent to sum up the quiz, because it's over. 
                
            RULE 3: If the quiz is just starting ({state.current_question} = None), OR if you just displayed an oracler response from Rule 5:
                    Your one and only action is to immediately call the generator agent. Do not write any text. Do not wait.
                
            RULE 4: If the user just provided an answer to a question, follow these steps:

                - Call the oracler_tool and: 
                - Pass the user's answer as the user_answer parameter. 
                    - If question is multiple choice, make sure that you pass just the letter of the answer.
                    - If question is true or false, pass anything that looks like "true" e.g. T, true, etc. as "true" and anything that looks like "false" e.g. F, false, etc. as "false".
                    - If question is yes or no, pass anything that looks like "yes" e.g. Y, yes, etc. as "yes" and anything that looks like "no" e.g. N, no, etc. as "no".
                - Pass the correct answer from {state.current_question.correct_answer} as the correct_answer parameter. If question is multiple choice, make sure that you pass just the choice letter of the answer.
                - DO NOT provide any feedback to the user until after the oracler_tool returns.

            RULE 5: If the Oracler tool just returned results:
                    Extract the response from {state.current_outcome} and:
                    - if outcome is "correct": inform user about it saying e.g. "Correct! You got it right!" or "Nice, that's the correct answer!"                    
                    - if outcome is "incorrect": inform user about it saying e.g. "Incorrect! The correct answer is {state.current_question.correct_answer}." and provide the explanation from {state.current_question.explanation}, so the user can learn.
                    - CRITICAL: Do NOT make up explanations. Use ONLY the explanation from the state.
                    - if difficulty was changed, inform user about it. do not change difficulty if it was not changed!
                    - then proceed to call generator agent to generate the next question

            CRITICAL: Follow these rules precisely. Your primary function is to call the correct agent based on the current state of the quiz and properly display Oracler responses to users.     
                    """,
    description="Orchestrates a dynamic difficulty quiz by guiding the user through questions one at a time based on a clear, state-driven logic.",
    sub_agents=[generator, summariser],
    tools=[oracler_tool],
)
    
