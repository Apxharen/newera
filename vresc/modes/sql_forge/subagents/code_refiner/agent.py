"""
Code Refiner Agent - Refines BigQuery SQL based on validation feedback or exits the refinement loop.

This agent works in conjunction with the TerminationCheckerAgent in a loop:
1. TerminationCheckerAgent validates SQL and provides feedback
2. CodeRefinerAgent either refines the SQL or exits if validation passed
"""

from __future__ import annotations
from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext
from google.genai import types

# Define the exact phrase the TerminationCheckerAgent should use to signal completion
COMPLETION_PHRASE = "SQL syntax validation passed."

def exit_loop(tool_context: ToolContext):
    """Call this function ONLY when validation indicates SQL is syntactically correct, signaling the refinement process should end."""
    print(f"  [Tool Call] exit_loop triggered by {tool_context.agent_name}")
    tool_context.actions.escalate = True
    # Return empty dict as tools should return JSON-serializable output
    return {}

# Code Refiner Agent (Inside the Refinement Loop)
code_refiner_agent = LlmAgent(
    name="CodeRefinerAgent",
    model="gemini-2.5-flash",
    include_contents='none',
    instruction=f"""You are a BigQuery SQL Refiner responsible for improving SQL based on validation feedback OR exiting the refinement process.

**Current Generated SQL:**
```sql
{{generated_sql}}
```

**Validation Feedback:**
{{validation_feedback}}

**Database Schema Available:** {{artifact.db_schema.txt}}

**Task:**
Analyze the 'Validation Feedback' carefully.

IF the validation feedback contains *exactly* the phrase "{COMPLETION_PHRASE}":
You MUST call the 'exit_loop' function immediately. Do not output any text.

ELSE (the validation feedback contains syntax errors or improvement suggestions):
Carefully refine the SQL to address the specific issues mentioned in the validation feedback. Focus on:
- Fixing syntax errors identified by the validator
- Correcting table/column name issues
- Improving JOIN conditions if mentioned
- Addressing any BigQuery-specific syntax problems
- Maintaining the original intent of the query

Output *only* the refined SQL query in proper BigQuery format with appropriate comments.

Example refined output format:
```sql
-- Fixed query based on validation feedback: [brief description of fix]
SELECT 
    c.customer_id,
    c.first_name,
    SUM(o.total_amount) AS total_spent
FROM 
    customers c
JOIN 
    orders o ON c.customer_id = o.customer_id
GROUP BY 
    c.customer_id, c.first_name
ORDER BY 
    total_spent DESC
LIMIT 10;
```

Do not add explanations outside the SQL. Either output the refined SQL OR call the exit_loop function.
""",
    description="Refines BigQuery SQL based on validation feedback, or calls exit_loop if SQL is syntactically valid.",
    tools=[exit_loop],
    output_key="generated_sql"  # Overwrites the generated_sql with refined version
)