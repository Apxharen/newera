from __future__ import annotations
from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext
from google.genai import types

# Define the exact phrase to signal completion - must match CodeRefinerAgent
COMPLETION_PHRASE = "SQL syntax validation passed."





# Termination Checker Agent (Inside the Refinement Loop) - Now an LLM Agent providing feedback
termination_checker_agent = LlmAgent(
    name="TerminationCheckerAgent",
    model="gemini-2.5-flash",
    include_contents='none',
    instruction=f"""You are a BigQuery SQL Validation Agent responsible for checking SQL syntax and providing feedback.

**Generated SQL to Validate:**
```sql
{{generated_sql}}
```

**Database Schema Available:** {{artifact.db_schema.txt}}

**Task:**
Validate the SQL query for BigQuery syntax correctness.

IF the SQL is syntactically correct for BigQuery (proper syntax, valid table/column references, correct BigQuery functions):
Respond *exactly* with the phrase "{COMPLETION_PHRASE}" and nothing else.

ELSE IF there are syntax errors, invalid table/column names, or BigQuery-specific issues:
Provide specific, actionable feedback about what needs to be fixed. Focus on:
- Syntax errors (missing commas, incorrect keywords, etc.)
- Invalid table or column references based on the schema
- BigQuery-specific function usage issues
- JOIN condition problems
- Aggregation or GROUP BY issues

Example feedback format:
"Missing comma after column 'customer_id' in SELECT clause. Table name 'customer' should be 'customers' based on schema. BigQuery requires explicit column list in GROUP BY when using aggregate functions."

Be specific and actionable. Output only the validation feedback OR the exact completion phrase.
""",
    description="Validates BigQuery SQL syntax and provides specific feedback or signals completion.",
    output_key="validation_feedback"
)