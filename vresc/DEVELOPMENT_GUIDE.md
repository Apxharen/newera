# Vresc Financial Intelligence System - Development Guide

## 📋 Project Overview

The **Vresc Financial Intelligence System** is a sophisticated FastAPI-based web application that provides an intelligent financial trading assistant powered by Google's Agent Development Kit (ADK). The system features a custom web interface replacing ADK Web, with advanced quiz capabilities, market commentary, and multi-agent orchestration using a **mode-based architecture**.

### 🎯 Core Capabilities
- **Adaptive Financial Quiz System** - Dynamic difficulty scaling with intelligent answer analysis
- **Real-time Market Commentary** - Live financial data integration and professional email-ready analysis  
- **BigQuery SQL Forge** - Iterative SQL generation with syntax validation and code review
- **Mode-Based Architecture** - Organized agent system with quiz, commentary, and SQL forge modes
- **Custom Web Interface** - Modern, responsive UI with minimalist design
- **Google Cloud Vertex AI Integration** - Enterprise-grade LLM capabilities

## 🏗️ System Architecture

### **Mode-Based Agent Hierarchy**
```
RootAgent (Brain/Orchestrator)
├── Quiz Mode
│   ├── QuizManager (Quiz orchestration & answer analysis)
│   └── Subagents/
│       ├── Generator (Question generation & formatting)
│       └── Summariser (Quiz completion & email simulation)
├── Commentary Mode
│   ├── CommenterAgent (Market analysis & financial insights)
│   └── Subagents/
│       ├── NewssummaryAgent (Financial news gathering)
│       └── FinanceMarketsAgent (Market data collection)
└── SQL Forge Mode
    ├── SqlForgeManager (SQL generation orchestration)
    └── Subagents/
        ├── CodeGeneratorAgent (Initial BigQuery SQL generation)
        ├── SqlRefinementLoop (Iterative validation & refinement)
        │   ├── TerminationCheckerAgent (SQL validation & feedback)
        │   └── CodeRefinerAgent (SQL refinement & loop exit)
```

### **Technology Stack**
- **Backend**: FastAPI, Python 3.8+
- **AI Framework**: Google ADK (Agent Development Kit)
- **LLM Provider**: Google Cloud Vertex AI (Gemini models)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Data Sources**: Yahoo Finance (yfinance), RSS feeds, Financial APIs
- **Session Management**: In-memory services (ADK built-in)

## 🔧 Technical Implementation

### **1. FastAPI Application Structure**

**File**: `main.py` (491 lines)

**Key Components**:
- **Session Management**: `InMemorySessionService` for conversation tracking
- **Artifact Storage**: `InMemoryArtifactService` for file management  
- **Memory Service**: `InMemoryMemoryService` for long-term knowledge
- **Runner Configuration**: ADK `Runner` with custom `RunConfig`
- **Event Processing**: Custom event extraction and formatting pipeline

**Critical Implementation Details**:
```python
# Robust event processing with null safety
parts = getattr(event.content, 'parts', None)
if not parts:
    continue

for part in parts:
    if not part:  # Skip None parts
        continue
    # Safe text extraction...
```

**Response Formatting Pipeline**:
- Multiple choice questions: Use bullet points `•` (agent provides a,b,c,d)
- True/False questions: Simple bullet format without letters
- Market commentary: Bold headers with structured formatting
- Quiz feedback: Bold text for "Correct!" messages

### **2. Root Agent Configuration**

**Root Agent** (`agent.py`):
```python
APP_NAME = "vresc-app"
MODEL_GEMINI = "gemini-2.5-flash"  # User preference: avoid "vertexai/" prefix

root_agent = Agent(
    name="rootagent",  # CRITICAL: Must remain "rootagent" for ADK compatibility
    description="The central brain of the Vresc Financial Intelligence System",
    # Orchestrates between quiz and commentary modes
)
```

**Import Structure**:
```python
from modes.quiz.agent import quiz_manager
from modes.commentary.agent import commenter_agent
```

**State Management Tool**:
- `state_change` tool handles intent routing (`start_quiz`, `start_commentary`)
- Delegates to appropriate mode agents based on user intent

### **3. Quiz Mode Implementation**

**Location**: `modes/quiz/`

**QuizManager** (`modes/quiz/agent.py`):
- **Difficulty Scaling**: Dynamic adjustment based on performance
- **Answer Analysis**: `oracler_tool` compares user answers to correct answers
- **Session State Tracking**: Questions asked, points scored, current difficulty
- **Rule-Based Logic**: 5 priority rules for quiz flow control

**Generator** (`modes/quiz/subagents/generator/agent.py`):
- **JSON Output Parsing**: `modify_response` callback processes LLM JSON
- **Question Storage**: Stores structured data in `session_state["current_question"]`
- **Format Requirements**: `correct_answer` as letter ("a", "b", "c", "d") or boolean

**Summariser** (`modes/quiz/subagents/summariser/agent.py`):
- **Performance Analytics**: Comprehensive quiz performance summaries
- **Email Integration**: Placeholder for future email functionality

**Key Session State Structure**:
```python
session_state = {
    "q_state": True,
    "no_q_asked": 1,
    "no_q_answered": 0,
    "current_question": {
        "question": "Question text...",
        "correct_answer": "c",  # Letter format
        "options": ["a) Option 1", "b) Option 2", ...],
        "explanation": "Detailed explanation..."
    },
    "points_scored": 0,
    "answers": ["correct"],
    "difficulty": "medium"
}
```

### **4. Commentary Mode Implementation**

**Location**: `modes/commentary/`

**CommenterAgent** (`modes/commentary/agent.py`):
- **Professional Email Generation**: Email-ready market commentary
- **Data Synthesis**: Combines news and market data
- **Workflow Orchestration**: Manages news and market data collection

**NewsummaryAgent** (`modes/commentary/subagents/newssummary/agent.py`):
- **RSS Feed Processing**: Yahoo Finance and financial news sources
- **Content Extraction**: Full article content retrieval
- **Time-sensitive Data**: Recent news filtering (8-hour window)

**FinanceMarketsAgent** (`modes/commentary/subagents/financemarkets/agent.py`):
- **Market Data Integration**: Yahoo Finance API (`yfinance`)
- **Multi-asset Coverage**: Indices, forex, crypto, commodities
- **Performance Analysis**: Percentage changes and trend analysis

**Commentary Session State**:
```python
session_state = {
    "commentary_state": True,
    "finance_markets_data": {},  # Market data from FinanceMarketsAgent
    "news_summary_data": {}      # News data from NewsummaryAgent
}
```

### **5. SQL Forge Mode Implementation**

**Location**: `modes/sql_forge/`

**SqlForgeManager** (`modes/sql_forge/agent.py`):
- **Schema Loading**: `load_schema_tool` loads database schemas from `data/schemas/`
- **Initial Generation**: Calls `CodeGeneratorAgent` via AgentTool for one-time SQL creation
- **Iterative Refinement**: Calls `SqlRefinementLoop` LoopAgent via AgentTool for validation and refinement
- **Intent Parsing**: Extracts database names from user requests
- **Error Handling**: Graceful handling of missing schemas with available options

**CodeGeneratorAgent** (`modes/sql_forge/subagents/code_generator/agent.py`):
- **Initial SQL Creation**: Generates first version of BigQuery SQL based on user requirements
- **Schema Integration**: Uses loaded schema artifacts for accurate table/column references
- **One-Time Execution**: Runs once as direct sub-agent, not within refinement loop
- **Best Practices**: Follows SQL optimization and formatting standards

**TerminationCheckerAgent** (`modes/sql_forge/subagents/termination_checker/agent.py`):
- **LlmAgent Implementation**: Validates SQL and provides specific feedback
- **Syntax Validation**: Analyzes BigQuery syntax, table/column references, and functions
- **Feedback Generation**: Provides actionable feedback for SQL improvements
- **Completion Signal**: Outputs exact phrase when SQL is syntactically correct

**CodeRefinerAgent** (`modes/sql_forge/subagents/code_refiner/agent.py`):
- **SQL Refinement**: Improves SQL based on validation feedback
- **Loop Exit Control**: Calls `exit_loop` tool when validation passes
- **Error Resolution**: Addresses syntax errors, table/column issues, and optimization opportunities
- **Intent Preservation**: Maintains original query purpose while fixing issues

**SQL Forge Session State**:
```python
session_state = {
    "current_database": "ecommerce",           # Loaded database schema
    "schema_loaded": True,                     # Schema loading status
    "generated_sql": "SELECT...",              # Current/refined SQL query
    "validation_feedback": "Missing comma..."  # Validation feedback from TerminationCheckerAgent
}
```

**Validator-Refiner Pattern**:
- **Initial Generation**: CodeGeneratorAgent creates first SQL version
- **Iterative Validation**: TerminationCheckerAgent validates and provides specific feedback
- **Iterative Refinement**: CodeRefinerAgent improves SQL or exits when valid
- **Max Iterations**: 10 iterations maximum to prevent infinite loops
- **Deterministic Exit**: `exit_loop` tool provides clear termination condition

## 🎨 UI/UX Design System

### **Design Philosophy**
- **Minimalist Aesthetic**: Clean white/silver/grey color palette
- **Professional Appearance**: Premium financial intelligence platform feel
- **Geometric Iconography**: Custom symbols (◈ ◆ ◇) replacing emojis
- **Responsive Layout**: Centered chat with fixed sidebar

### **Color Palette**
```css
/* Primary Colors */
--primary-bg: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #cbd5e1 100%);
--text-primary: #374151;
--accent-silver: #e2e8f0;
--icon-grey: #d1d5db;
--hover-white: #f9fafb;

/* Interactive Elements */
--button-gradient: linear-gradient(135deg, #e2e8f0, #cbd5e1);
--hover-gradient: linear-gradient(135deg, #94a3b8, #64748b);
```

### **Icon System**
- **◈** - Primary brand icon (diamond with center)
- **◆** - Secondary features (filled diamond)  
- **◇** - Tertiary elements (hollow diamond)

### **Layout Structure**
```html
<div class="app-container">
    <div class="sidebar">
        <!-- Minimalist icons with hover tooltips -->
    </div>
    <div class="chat-container">
        <!-- Centered chat interface -->
    </div>
</div>
```

## ⚙️ Configuration & Environment

### **Required Environment Variables**
```bash
# Google Cloud Vertex AI (REQUIRED)
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"  # Auto-set if missing
```

### **Virtual Environment Setup**
```bash
# Project uses Python .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### **Startup Script** (`start_server.sh`)
- Automatic environment validation
- Virtual environment activation
- Vertex AI configuration checks
- FastAPI server launch on port 8001

## 🐛 Known Issues & Solutions

### **1. 'NoneType' object has no attribute 'parts' Error**
**Solution**: Comprehensive null checking implemented:
```python
# Multiple layers of defensive programming
if not hasattr(event.content, 'parts'):
    continue
    
parts = getattr(event.content, 'parts', None)
if not parts:
    continue

try:
    for part in parts:
        if not part:  # Skip None parts
            continue
        # Safe processing...
except (TypeError, AttributeError) as parts_error:
    # Handle gracefully
```

### **2. Import Path Issues After Reorganization**
**Issue**: Relative imports failing with new mode structure  
**Solution**: Use absolute imports throughout:
```python
# Updated import structure
from modes.quiz.agent import quiz_manager
from modes.commentary.agent import commenter_agent
```

### **3. Mode Agent Import Structure**
**Issue**: Subagent imports within modes  
**Solution**: Updated relative imports within modes:
```python
# Quiz mode imports
from .subagents.generator.agent import generator
from .subagents.summariser.agent import summariser

# Commentary mode imports
from .subagents.newssummary.agent import news_summary_agent
from .subagents.financemarkets.agent import finance_markets_agent
```

### **4. Double Letter Labels in Multiple Choice**
**Issue**: Agent provides "a) Option" but formatter added "a)" again  
**Solution**: Removed automatic letter addition, use bullet points only

## 📁 File Structure

```
vresc/
├── main.py                    # FastAPI application (491 lines)
├── agent.py                   # Root agent definition (94 lines)
├── start_server.sh            # Startup script (62 lines)
├── requirements.txt           # Python dependencies
├── README.md                  # User documentation (205 lines)
├── DEVELOPMENT_GUIDE.md       # This file (380 lines)
├── static/
│   └── index.html            # Web interface (712 lines)
├── modes/                     # Mode-based architecture
│   ├── quiz/                  # Financial Knowledge Assessment Mode
│   │   ├── agent.py          # Quiz Manager (127 lines)
│   │   ├── __init__.py       # Module initialization
│   │   ├── README.md         # Comprehensive quiz mode documentation
│   │   └── subagents/        # Quiz-specific agents
│   │       ├── generator/    # Question generation
│   │       │   ├── agent.py  # Generator agent (115 lines)
│   │       │   └── __init__.py
│   │       └── summariser/   # Quiz summaries
│   │           ├── agent.py  # Summariser agent (50 lines)
│   │           └── __init__.py
│   ├── commentary/           # Financial Market Commentary Mode
│   │   ├── agent.py          # Commentary Manager (53 lines)
│   │   ├── __init__.py       # Module initialization
│   │   ├── README.md         # Comprehensive commentary mode documentation
│   │   └── subagents/        # Commentary-specific agents
│   │       ├── newssummary/  # Financial news gathering
│   │       │   ├── agent.py  # News agent (144 lines)
│   │       │   └── __init__.py
│   │       └── financemarkets/ # Market data collection
│   │           ├── agent.py   # Markets agent (249 lines)
│   │           └── __init__.py
│   └── sql_forge/            # BigQuery SQL Generation Mode
│       ├── __init__.py       # Module initialization
│       ├── agent.py          # SqlForgeManager + load_schema_tool
│       ├── README.md         # Comprehensive SQL forge mode documentation
│       └── subagents/        # SQL generation specialists
│           ├── __init__.py
│           ├── sql_refinement_loop/ # Iterative refinement orchestrator
│           │   ├── __init__.py
│           │   └── agent.py       # SqlRefinementLoop (LoopAgent)
│           ├── code_generator/    # SQL generation
│           │   ├── __init__.py
│           │   └── agent.py       # CodeGeneratorAgent
│           ├── code_reviewer/     # Code review & critique
│           │   ├── __init__.py
│           │   └── agent.py       # CodeReviewerAgent
│           └── termination_checker/ # Syntax validation & loop control
│               ├── __init__.py
│               └── agent.py       # TerminationCheckerAgent
├── data/
│   ├── finance.pdf           # Training data
│   ├── finance233.pdf        # Additional training data
│   ├── summary.txt           # Content summary
│   ├── full_text.txt         # Full text content
│   └── schemas/              # Database schemas for SQL Forge mode
│       └── ecommerce.txt     # Sample e-commerce database schema
└── services/
    └── __init__.py           # Service initialization
```

## 🔍 Key Code Patterns

### **1. Event Processing Pattern**
```python
# Standard event extraction pattern used throughout
for event in events:
    try:
        if event.author == "user" or not event.content:
            continue
        
        parts = getattr(event.content, 'parts', None)
        if not parts:
            continue
            
        # Process parts safely...
    except Exception as e:
        # Log and continue gracefully
        continue
```

### **2. Mode Agent Import Pattern**
```python
# Root agent imports
from modes.quiz.agent import quiz_manager
from modes.commentary.agent import commenter_agent

# Mode-specific subagent imports
from .subagents.generator.agent import generator
from .subagents.summariser.agent import summariser
```

### **3. Tool Definition Pattern**
```python
async def tool_name(param: str, tool_context: ToolContext) -> str:
    """Tool description for LLM understanding."""
    try:
        # Tool implementation with session state access
        tool_context.state["key"] = "value"
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

### **4. Response Formatting Pattern**
```python
def format_response_for_web(text: str) -> str:
    """Consistent formatting for all response types."""
    # Question detection and formatting
    # Option formatting (bullets vs letters)
    # Bold text for important information
    return formatted_text
```

## 📦 Dependencies

### **Core Requirements**
```txt
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
google-adk>=0.5.0
pydantic>=2.0.0
python-multipart
yfinance>=0.2.18
feedparser>=6.0.0
beautifulsoup4>=4.12.0
requests>=2.31.0
pandas>=2.0.0
python-bigquery-validator  # For SQL Forge mode syntax validation
```

### **Google Cloud Requirements**
- Authenticated `gcloud` CLI
- Vertex AI API enabled
- Project with Gemini model access

## 🚀 Deployment Instructions

### **Local Development**
```bash
# 1. Clone and setup
cd vresc/
source .venv/bin/activate

# 2. Configure environment
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT="your-project-id"

# 3. Start server
./start_server.sh
```

### **Production Considerations**
- **Session Persistence**: Consider Redis for session storage
- **Artifact Storage**: Consider Google Cloud Storage
- **Monitoring**: Implement health checks and logging
- **Security**: Add authentication and rate limiting
- **Scaling**: Consider Cloud Run deployment

## 📚 Mode Documentation

### **Quiz Mode**
**Location**: `modes/quiz/README.md`

**Comprehensive Coverage**:
- Architecture overview with Quiz Manager + subagents
- State management system (9 state variables)
- Rule-based workflow logic (5 priority rules)
- Difficulty adaptation algorithm
- Question types (multiple choice, true/false, yes/no)
- Integration points and error handling
- Future enhancement roadmap

### **Commentary Mode**
**Location**: `modes/commentary/README.md`

**Comprehensive Coverage**:
- Professional market analysis workflow
- Data flow architecture with session state
- Real-time news and market data collection
- Email-ready output formatting
- Multi-source integration (Yahoo Finance, RSS feeds)
- Security & compliance considerations
- Performance optimization strategies

### **SQL Forge Mode**
**Location**: `modes/sql_forge/README.md`

**Comprehensive Coverage**:
- Validator-refiner pattern for iterative SQL improvement
- Initial SQL generation followed by validation-refinement loop
- BigQuery syntax validation and specific feedback generation
- Schema-driven SQL generation from data/schemas/ directory
- Iterative refinement based on validation feedback
- Deterministic loop termination via exit_loop tool
- LlmAgent-based validation and refinement approach
- Multi-agent orchestration with specialized subagents
- Schema artifact management and session state tracking

## 🎯 Branding Evolution

### **Timeline**
1. **Quiz Agent** → **Phoenix** (red elements)
2. **Phoenix** → **Vresc** (purple elements) 
3. **Vresc** → **Final** (white/silver elements)

### **Final Brand Identity**
- **Name**: Vresc Financial Intelligence System
- **Subtitle**: "Trading Assistant"
- **Icon**: ◈ (geometric diamond symbol)
- **Color Theme**: White/silver/grey professional palette
- **Positioning**: Premium financial intelligence platform

## 📝 Development Notes

### **User Preferences** (Critical for Future Work)
- Keep `rootagent` name for ADK compatibility (never rename)
- Use `gemini-2.5-flash` model (avoid "vertexai/" prefix)
- Agent provides a,b,c,d labels - don't add them in formatter
- True/False questions use bullets, not letters
- White/silver/grey color scheme only
- Geometric symbols instead of emojis
- Professional, minimalist design aesthetic

### **Architecture Decisions**
- **Mode-Based Organization**: Separated quiz and commentary into distinct modes
- **FastAPI over ADK Web**: Custom interface for better control
- **In-Memory Services**: Suitable for development, consider persistence for production
- **Multi-Agent Design**: Specialized agents for better modularity
- **Event-Based Processing**: Mirrors ADK Web behavior for consistency

### **Reorganization Benefits**
- **Clear Separation of Concerns**: Each mode has its own agents and documentation
- **Scalable Architecture**: Easy to add new modes (e.g., portfolio management)
- **Comprehensive Documentation**: Detailed README for each mode
- **Clean Import Structure**: Logical import hierarchy
- **Future-Proof Design**: Extensible for additional financial capabilities

### **Future Enhancement Opportunities**
- Add user authentication system
- Implement persistent session storage
- Expand financial data sources
- Add more quiz question types
- Implement advanced trading analytics
- Add portfolio management features
- Create additional modes (e.g., risk analysis, compliance)

## 🔧 Development Workflow

### **Adding New Modes**
1. Create new mode folder in `modes/`
2. Implement mode agent and subagents
3. Add mode imports to root agent
4. Update `state_change` tool for new intent
5. Create comprehensive README for the mode
6. Update this development guide

### **Mode Development Guidelines**
- Each mode should have its own agent.py and __init__.py
- Subagents should be organized in subagents/ folder
- Comprehensive documentation in README.md
- Clear session state management
- Error handling and graceful degradation

### **Testing Strategy**
- Unit tests for individual agents
- Integration tests for mode workflows
- End-to-end testing via web interface
- Performance testing for data-heavy operations

---

**Last Updated**: January 2025  
**System Version**: 2.0.0 (Mode-Based Architecture)  
**Documentation Author**: AI Assistant  
**Target Audience**: Future developers and AI systems working on this codebase