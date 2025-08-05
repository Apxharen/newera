"""
SQL Refinement Loop Agent - A LoopAgent that orchestrates iterative SQL generation and refinement.

This LoopAgent runs a continuous loop of:
1. CodeGeneratorAgent - Generates BigQuery SQL based on user request and schema
2. CodeReviewerAgent - Reviews the generated SQL for correctness and efficiency  
3. TerminationCheckerAgent - Validates SQL syntax and terminates loop when valid

The loop continues until the TerminationCheckerAgent determines the SQL is syntactically correct
or max_iterations is reached.
"""

from google.adk.agents import LoopAgent
from ..termination_checker.agent import termination_checker_agent
from ..code_refiner.agent import code_refiner_agent

# Create the SQL Refinement Loop Agent
sql_refinement_loop = LoopAgent(
    name="SqlRefinementLoop",
    description="Orchestrates iterative SQL validation and refinement until syntactically valid SQL is produced",
    sub_agents=[
        termination_checker_agent,  # Validates SQL and provides feedback
        code_refiner_agent          # Refines SQL based on feedback or exits loop
    ],
    max_iterations=10  # Prevent infinite loops - max 10 refinement cycles
)