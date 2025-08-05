from __future__ import annotations
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types
import os
from .subagents.sql_refinement_loop.agent import sql_refinement_loop
from .subagents.code_generator.agent import code_generator_agent


async def load_schema_tool(database_name: str, tool_context: ToolContext) -> str:
    """
    Load a specific database schema from the local data/schemas/ directory and save it as a session artifact.
    
    Args:
        database_name: Name of the database schema file to load (without .txt extension)
        tool_context: Tool context for accessing session state and saving artifacts
        
    Returns:
        Success or error message
    """
    try:
        # Get the correct path relative to the vresc directory
        # Current file: vresc/modes/sql_forge/agent.py -> go up 3 levels to vresc/
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        schema_file_path = os.path.join(script_dir, "data", "schemas", f"{database_name}.txt")
        schemas_dir = os.path.join(script_dir, "data", "schemas")
        
        # Check if file exists
        if not os.path.exists(schema_file_path):
            available_schemas = []
            if os.path.exists(schemas_dir):
                available_schemas = [f.replace('.txt', '') for f in os.listdir(schemas_dir) if f.endswith('.txt')]
            
            return f"Error: Schema file '{database_name}.txt' not found. Available schemas: {', '.join(available_schemas) if available_schemas else 'None'}"
        
        # Read the schema file content as binary (following quiz mode pattern)
        with open(schema_file_path, 'rb') as file:
            schema_bytes = file.read()
        
        if not schema_bytes:
            return f"Error: Schema file '{database_name}.txt' is empty"
            
        # Create a google.genai.types.Part from the file content (following quiz mode pattern)
        schema_part = types.Part.from_bytes(data=schema_bytes, mime_type="text/plain")
        
        # Save as session artifact (following quiz mode pattern)
        await tool_context.save_artifact(filename='db_schema.txt', artifact=schema_part)
        
        # Also store database name in session state for reference
        tool_context.state["current_database"] = database_name
        tool_context.state["schema_loaded"] = True
        
        return f"Success: Schema for database '{database_name}' loaded and saved as artifact 'db_schema.txt'. Schema contains {len(schema_bytes)} bytes."
        
    except Exception as e:
        return f"Error loading schema: {str(e)}"


# Create AgentTools for the components
code_generator_tool = AgentTool(code_generator_agent)
sql_refinement_tool = AgentTool(sql_refinement_loop)

sql_forge_manager = LlmAgent(
    name="SqlForgeManager",
    model="gemini-2.5-flash",
    instruction="""
    You are the SQL Forge Manager responsible for orchestrating the BigQuery SQL Forge process.
    
    Your workflow:
    1. Parse the user's request to identify the database_name they want to work with
    2. Call the load_schema_tool with the extracted database_name
    3. After the schema is successfully loaded, ask user what exactly they want to do with the database 
    4. Once user has specified what they want to do:
       a. Call the CodeGeneratorAgent tool to generate the initial BigQuery SQL
       b. Call the SqlRefinementLoop tool to iteratively refine the SQL until it's syntactically valid
    
    The SqlRefinementLoop will use these sub_agents in order:
    - TerminationCheckerAgent: Validates SQL syntax and provides specific feedback
    - CodeRefinerAgent: Refines SQL based on feedback or exits loop when SQL is valid
    
    Instructions for parsing database_name:
    - Look for explicit database names in the user's request (e.g., "use ecommerce database", "query the sales_db")
    - If no explicit database is mentioned, ask the user to specify which database schema they want to use
    - Common database names might include: ecommerce, sales, inventory, analytics, etc.
    
    Example user requests:
    - "Generate SQL for the ecommerce database to find top customers"
    - "Create a BigQuery query using sales_db to calculate monthly revenue"
    - "Help me write SQL for the inventory database"
    
    Workflow sequence:
    1. load_schema_tool(database_name) → loads schema as artifact
    2. CodeGeneratorAgent(user_request) → generates initial SQL 
    3. SqlRefinementLoop(user_request) → validates and refines SQL until syntactically correct
    """,
    description="Orchestrates BigQuery SQL generation by loading database schemas and managing the iterative refinement loop.",
    tools=[FunctionTool(load_schema_tool), code_generator_tool, sql_refinement_tool]
)