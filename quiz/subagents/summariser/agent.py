from google.adk.agents import Agent

summariser = Agent(
    name="Summariser",
    model="gemini-2.5-flash",
    instruction="""You are the summariser. Your main role is to summarise the quiz.
    You will be given the session state and you must summarise the quiz.
    You must use the tools to get the information you need to summarise the quiz.
    Suggest to the user pontetial areas of improvement. Check where they made mistakes.
    You'll see that in `state.user_result_q_no` fields from the session state""",
    description="Summarises the quiz",
)