from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext

# TOOLS
async def send_summary_email_tool(summary_text: str, tool_context: ToolContext) -> str:
    """
    Placeholder tool for sending quiz summary to a predefined email address.
    In the future, this will be implemented to actually send emails.
    
    Args:
        summary_text: The complete quiz summary text to be sent via email
    
    Returns:
        A status message indicating the email sending result
    """
    
    # TODO: Future implementation will include:
    # - Email service integration (Gmail API, SendGrid, etc.)
    # - Predefined recipient email address configuration
    # - Email template formatting
    # - Error handling for email delivery failures
    
    # For now, this is a placeholder that logs the action
    print(f"[EMAIL PLACEHOLDER] Would send the following summary to predefined email:")
    print(f"Subject: Quiz Summary Report")
    print(f"Content:\n{summary_text}")
    print(f"[EMAIL PLACEHOLDER] Email sending simulated successfully")
    
    return {"status" : "success"}

summariser = Agent(
    name="Summariser",
    model="gemini-2.0-flash",
    instruction="""You are the summariser. Your main role is to summarise the quiz.
    You will be given the session state and you must summarise the quiz.
    
    After creating a comprehensive summary, you MUST call the send_summary_email_tool to send 
    the summary to a predefined email address (currently in placeholder mode).
    
    Your summary should include:
    - Overall quiz performance and score
    - Number of questions answered correctly/incorrectly
    - Difficulty level changes during the quiz
    - Specific areas where the user made mistakes
    - Suggestions for improvement based on incorrect answers
    
    Make sure to format the summary in a clear, readable way before sending it via email.""",
    description="Summarises the quiz and sends summary via email",
    tools=[send_summary_email_tool],
)