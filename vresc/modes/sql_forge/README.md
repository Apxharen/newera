# SQL Forge Mode - BigQuery SQL Generation & Refinement

## 📋 Overview

The **SQL Forge Mode** is an advanced BigQuery SQL generation system that implements an iterative refinement loop using a generator-critic pattern. This mode helps users generate syntactically valid and efficient BigQuery SQL queries based on database schemas and natural language requirements.

### 🎯 Core Capabilities
- **Schema-Driven SQL Generation** - Generates SQL based on loaded database schemas
- **Iterative Refinement Loop** - Generator-critic pattern for continuous improvement
- **Syntax Validation** - Deterministic termination when SQL is syntactically valid
- **Performance Optimization** - Code review for efficiency and best practices
- **Multi-Agent Orchestration** - Specialized agents for each step of the process

## 🏗️ System Architecture

### **Agent Hierarchy**
```
SqlForgeManager (Primary Orchestrator)
├── Schema Loading (load_schema_tool)
├── CodeGeneratorAgent (Initial SQL Generation)
└── SqlRefinementLoop (LoopAgent)
    ├── TerminationCheckerAgent (Validation & Feedback)
    └── CodeRefinerAgent (Refinement & Loop Exit)
```

### **Workflow Process**
1. **Schema Loading**: User specifies database, manager loads schema from `data/schemas/`
2. **Initial Generation**: CodeGeneratorAgent creates first version of BigQuery SQL
3. **Iterative Refinement Loop**:
   - **Validation**: TerminationCheckerAgent validates SQL and provides specific feedback
   - **Refinement**: CodeRefinerAgent either refines SQL based on feedback OR exits when valid
4. **Termination**: Loop exits when SQL is syntactically correct (max 10 iterations)

## 🔧 Technical Implementation

### **1. SqlForgeManager** (`agent.py`)

**Primary Orchestrator Agent**
- **Model**: `gemini-2.5-flash`
- **Purpose**: Parse user requests, load schemas, manage refinement loop
- **Key Tool**: `load_schema_tool`

**Responsibilities**:
- Extract `database_name` from user requests
- Load appropriate schema from `data/schemas/{database_name}.txt`
- Call `CodeGeneratorAgent` for initial SQL generation
- Run `SqlRefinementLoop` for iterative refinement until SQL is valid
- Handle schema loading errors and provide available options

**Schema Loading Tool**:
```python
async def load_schema_tool(database_name: str, tool_context: ToolContext) -> str:
    # Loads schema file and saves as artifact {artifact.db_schema.txt}
    # Stores database_name and schema_loaded flags in session state
```

### **2. CodeGeneratorAgent** (`subagents/code_generator/agent.py`)

**Initial BigQuery SQL Generation**
- **Model**: `gemini-2.5-flash`
- **Type**: Direct sub-agent of SqlForgeManager (runs ONCE)
- **Input**: Database schema artifact + user requirements
- **Output**: Generated BigQuery SQL (stored as `generated_sql` in session state)

**Generation Guidelines**:
- Uses proper BigQuery syntax and functions
- Follows SQL best practices (proper joins, meaningful aliases)
- Includes explanatory comments for complex logic
- Considers performance implications
- Creates first version based on user requirements

**Key Features**:
- Schema artifact integration: `{artifact.db_schema.txt}`
- One-time execution for initial SQL creation
- Proper formatting with comments
- BigQuery-specific optimizations

### **3. TerminationCheckerAgent** (`subagents/termination_checker/agent.py`)

**SQL Validation & Feedback Provider**
- **Type**: LlmAgent (within SqlRefinementLoop)
- **Model**: `gemini-2.5-flash`
- **Purpose**: Validate SQL syntax and provide specific feedback
- **Output**: Validation feedback (stored as `validation_feedback` in session state)

**Validation Logic**:
- Analyzes generated SQL for BigQuery syntax correctness
- Checks table/column references against schema
- Validates JOIN conditions, aggregations, and BigQuery functions
- If valid → Outputs exact phrase: `"SQL syntax validation passed."`
- If invalid → Provides specific, actionable feedback

**Feedback Examples**:
- "Missing comma after column 'customer_id' in SELECT clause"
- "Table name 'customer' should be 'customers' based on schema"
- "BigQuery requires explicit column list in GROUP BY when using aggregate functions"

### **4. CodeRefinerAgent** (`subagents/code_refiner/agent.py`)

**SQL Refinement & Loop Exit Control**
- **Type**: LlmAgent (within SqlRefinementLoop)
- **Model**: `gemini-2.5-flash`
- **Purpose**: Refine SQL based on feedback OR exit loop when valid
- **Tool**: `exit_loop` (for termination)

**Refinement Logic**:
- Reads `validation_feedback` from TerminationCheckerAgent
- If feedback contains `"SQL syntax validation passed."` → Calls `exit_loop` tool
- If feedback contains specific issues → Refines SQL to address problems
- Outputs improved SQL maintaining original intent

**Exit Tool**:
```python
def exit_loop(tool_context: ToolContext):
    # Signals loop termination when SQL is syntactically correct
    tool_context.actions.escalate = True
```

**Refinement Focus**:
- Fixing syntax errors identified by validator
- Correcting table/column name issues
- Improving JOIN conditions and aggregations
- Maintaining query performance and readability

## 📁 File Structure

```
vresc/modes/sql_forge/
├── __init__.py                           # Module initialization
├── agent.py                              # SqlForgeManager + load_schema_tool (Primary orchestrator)
├── README.md                             # This comprehensive documentation
└── subagents/                            # Specialized sub-agents
    ├── __init__.py
    ├── code_generator/                   # Initial SQL generation
    │   ├── __init__.py
    │   └── agent.py                      # CodeGeneratorAgent
    ├── sql_refinement_loop/              # Iterative refinement orchestrator
    │   ├── __init__.py
    │   └── agent.py                      # SqlRefinementLoop (LoopAgent)
    ├── termination_checker/              # SQL validation & feedback
    │   ├── __init__.py
    │   └── agent.py                      # TerminationCheckerAgent (LlmAgent)
    └── code_refiner/                     # SQL refinement & loop exit
        ├── __init__.py
        └── agent.py                      # CodeRefinerAgent + exit_loop tool

vresc/data/schemas/                       # Database schema storage
├── ecommerce.txt                         # Sample e-commerce database schema
├── sales.txt                             # Sample sales database schema
└── [additional schemas...]               # User-defined database schemas
```

## 🔄 Session State Management

### **State Variables**

```python
session_state = {
    # Schema Management
    "current_database": "ecommerce",           # Currently loaded database
    "schema_loaded": True,                     # Schema loading status
    
    # SQL Generation & Refinement
    "generated_sql": "SELECT...",              # Current generated/refined SQL
    "validation_feedback": "Missing comma..." # Latest validation feedback from TerminationCheckerAgent
}
```

### **Artifacts**

- **`db_schema.txt`**: Loaded database schema content, accessible via `{artifact.db_schema.txt}`

## 🚀 Usage Examples

### **Example 1: Basic Query Generation**
```
User: "Generate SQL for the ecommerce database to find top 10 customers by total spending"

1. SqlForgeManager extracts "ecommerce" as database_name
2. load_schema_tool loads data/schemas/ecommerce.txt → artifact.db_schema.txt
3. CodeGeneratorAgent creates initial SQL with proper JOINs and aggregation
4. SqlRefinementLoop begins:
   - TerminationCheckerAgent validates SQL syntax → provides feedback if issues found
   - CodeRefinerAgent refines SQL based on feedback OR exits when valid
   - Loop continues until SQL is syntactically correct
```

### **Example 2: Complex Analytics Query**
```
User: "Create a BigQuery query using the ecommerce database to analyze monthly revenue trends by product category"

Process:
1. Schema loading for ecommerce database
2. Initial SQL generation with DATE functions and aggregation
3. Iterative validation and refinement:
   - TerminationCheckerAgent identifies syntax issues (e.g., missing column in GROUP BY)
   - CodeRefinerAgent fixes the issues and improves the query
   - Process repeats until BigQuery syntax validation passes
   - Final validated SQL ready for execution
```

## ⚙️ Configuration & Dependencies

### **Required Dependencies**
```txt
# Core ADK framework
google-adk==1.6.1

# SQL validation library
python-bigquery-validator

# Standard dependencies (already in requirements.txt)
pydantic
google-genai
```

### **Environment Setup**
```bash
# Install new dependency
pip install python-bigquery-validator

# Ensure Google Cloud Vertex AI is configured
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

### **Schema File Format**
Database schemas should be stored as `.txt` files in `data/schemas/` with the following format:

```
# Database Name Schema

## Table: table_name
- column_name (TYPE) - Description
- primary_key (INT) - Primary key description
- foreign_key (INT) - Foreign key to other_table

## Table: other_table
- id (INT) - Primary key
- name (STRING) - Description

## Common Queries Examples:
- Example query description
- Another query example
```

## 🐛 Error Handling & Edge Cases

### **Schema Loading Errors**
- **File Not Found**: Lists available schemas in `data/schemas/`
- **Empty Schema**: Returns error message with file path
- **Invalid Format**: Graceful handling with error details

### **SQL Generation Issues**
- **Missing Schema**: Requests schema loading before generation
- **Invalid Requirements**: Requests clarification from user
- **Generation Failure**: Provides error details and retry option

### **Validation Failures**
- **Library Import Error**: Falls back to basic SQL validation
- **Syntax Errors**: Provides specific error messages for refinement
- **Infinite Loop Prevention**: Maximum 5 iterations before forced termination

### **Fallback Validation**
When `python-bigquery-validator` is unavailable:
- Basic keyword validation (SELECT, FROM requirements)
- Parentheses matching
- Unsafe operation detection (DELETE, DROP, etc.)
- Empty query detection

## 🔍 Integration Points

### **Root Agent Integration**
The SQL Forge mode integrates with the main Vresc system through:

```python
# In main agent.py, import the SqlForgeManager
from modes.sql_forge.agent import sql_forge_manager

# SqlForgeManager is included as a sub_agent of root_agent
root_agent = Agent(
    sub_agents=[quiz_manager, commenter_agent, sql_forge_manager]
)

# Add to state_change tool for intent routing
elif intent == "start_sql_forge":
    tool_context.state["sql_forge_state"] = True
    # Root agent will delegate to SqlForgeManager automatically
```

### **Frontend Integration**
Add SQL Forge icon to FastAPI frontend:
```html
<!-- In static/index.html -->
<div class="mode-icon" onclick="startSQLForge()">
    ◈ SQL Forge
</div>
```

## 📈 Performance Considerations

### **Query Optimization**
- **Schema Caching**: Consider caching loaded schemas for repeated use
- **Validation Caching**: Cache validation results for identical queries
- **Loop Efficiency**: Maximum iteration limit prevents infinite loops

### **Memory Management**
- **Session State**: Monitor session state size for large SQL queries
- **Artifact Storage**: Clean up artifacts after mode completion
- **Error Logging**: Implement structured logging for debugging

## 🔮 Future Enhancements

### **Planned Features**
- **Multiple Database Support**: Load and compare multiple schemas
- **SQL Execution**: Optional query execution with sandboxing
- **Query Optimization**: Advanced performance tuning suggestions
- **Template Library**: Pre-built query templates for common patterns
- **Visual Schema**: Graphical database schema representation

### **Advanced Capabilities**
- **Explain Plan Analysis**: BigQuery execution plan optimization
- **Cost Estimation**: Query cost analysis and optimization
- **Security Validation**: SQL injection and security best practices
- **Version Control**: Track query evolution and rollback capabilities

## 🏷️ Mode Metadata

- **Mode Name**: SQL Forge
- **Version**: 1.0.0
- **Agent Count**: 4 (1 orchestrator + 3 subagents)
- **Primary Model**: gemini-2.5-flash
- **Loop Type**: LoopAgent with generator-critic pattern
- **Termination**: Deterministic (syntax validation)
- **Max Iterations**: 5
- **Dependencies**: python-bigquery-validator

## 📝 Development Notes

### **Architecture Decisions**
- **Generator-Critic Pattern**: Ensures iterative improvement of SQL quality
- **Deterministic Termination**: Syntax validation provides clear exit condition
- **Modular Design**: Each agent has a specific, well-defined responsibility
- **Schema Artifacts**: Efficient schema sharing across all agents
- **Fallback Validation**: Ensures functionality even without external libraries

### **Code Quality Standards**
- **Type Hints**: Full type annotation for all functions and methods
- **Error Handling**: Comprehensive exception handling with graceful degradation
- **Documentation**: Detailed docstrings and inline comments
- **Testing**: Validation logic tested with various SQL patterns
- **Logging**: Structured logging for debugging and monitoring

---

**Last Updated**: January 2025  
**Mode Status**: Complete - Ready for Integration  
**Next Steps**: Frontend integration and user testing  
**Documentation Author**: AI Assistant (SQL Forge Implementation)  
**Target Audience**: Developers and AI systems working on BigQuery SQL generation