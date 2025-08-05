# Quiz Agent FastAPI Interface

This is a custom FastAPI interface for the Quiz Agent System with a beautiful web frontend, replacing the ADK web interface with a custom implementation.

## Features

- **🌐 Web Frontend**: Beautiful, responsive chat interface
- **🔄 RESTful API**: Chat with the quiz agent via HTTP endpoints
- **💾 Session Management**: Persistent conversations using InMemorySessionService
- **📁 Artifact Storage**: Handle file uploads and artifacts using InMemoryArtifactService
- **☁️ Google Cloud Integration**: Uses Vertex AI via Google ADK
- **🎯 Interactive Quiz**: Adaptive difficulty financial knowledge quiz
- **📈 Market Commentary**: Real-time financial market analysis

## Setup

### 1. Prerequisites

- Python 3.8 or higher
- Virtual environment (already created in `.venv/`)
- Google Cloud Project with Vertex AI enabled
- Google Cloud CLI authenticated

### 2. Google Cloud Vertex AI Setup

The application is configured to use **Google Cloud Vertex AI** (not API keys):

```bash
# 1. Set your Google Cloud project
export GOOGLE_CLOUD_PROJECT='your-project-id'

# 2. Authenticate with Google Cloud
gcloud auth application-default login

# 3. Enable required APIs in your project
gcloud services enable aiplatform.googleapis.com
```

**Note**: The startup script automatically sets `GOOGLE_GENAI_USE_VERTEXAI=TRUE`

### 3. Running the Server

#### Quick Start
```bash
./start_server.sh
```

#### Manual Start
```bash
source .venv/bin/activate
python main.py
```

The server will start on `http://localhost:8001`

## Web Interface

### 🌐 Chat Interface
Visit `http://localhost:8001/` for the beautiful web interface featuring:

- **Real-time chat** with the quiz agent
- **Quick actions** for starting quiz or market commentary
- **Session management** with persistent conversations
- **Visual indicators** for loading states and errors
- **Responsive design** that works on desktop and mobile

### 🎯 Quick Start Options
- **Start Quiz**: Interactive financial knowledge quiz with adaptive difficulty
- **Market Commentary**: Get real-time financial market insights and news
- **General Chat**: Ask questions about finance, trading, or any topic

## API Endpoints

### Health Check
```bash
GET /health
```
Returns server status and service information.

### Chat with Agent
```bash
POST /chat
Content-Type: application/json

{
  "message": "Hello! I want to start a quiz.",
  "session_id": "optional-session-id"
}
```

Response:
```json
{
  "response": "Agent's response text",
  "session_id": "session-uuid",
  "artifacts": ["list", "of", "artifact", "ids"]
}
```

### Session Management
```bash
GET /sessions                    # List all sessions
GET /sessions/{session_id}       # Get session info
DELETE /sessions/{session_id}    # Delete session
```

### Artifacts
```bash
GET /artifacts/{session_id}/{filename}?version=1  # Get artifact
```

## Usage Examples

### Starting a Quiz
```bash
curl -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to start a quiz"}'
```

### Continuing a Conversation
```bash
curl -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "A", 
    "session_id": "your-session-id-from-previous-response"
  }'
```

### Check Server Health
```bash
curl -X GET "http://localhost:8001/health"
```

## Interfaces

### 🌐 Web Interface (Primary)
- **Main Interface**: http://localhost:8001/
- Beautiful, responsive chat interface
- Perfect for end users

### 📚 API Documentation
- **Swagger UI**: http://localhost:8001/docs  
- **ReDoc**: http://localhost:8001/redoc
- Perfect for developers and API integration

## Architecture

The FastAPI interface uses the following Google ADK components:

- **Runner**: Manages agent execution and lifecycle
- **InMemorySessionService**: Handles session persistence
- **InMemoryArtifactService**: Manages file storage
- **InMemoryMemoryService**: Handles agent memory
- **RunConfig**: Configures runtime behavior

## Agent Features

The Quiz Agent supports:

1. **Quiz Mode**: Interactive financial quiz with dynamic difficulty
2. **Commentary Mode**: Financial market analysis and news
3. **State Management**: Tracks quiz progress and scoring
4. **Multi-Agent System**: Uses specialized sub-agents for different tasks

## Configuration

The server is configured with:
- **AI Provider**: Google Cloud Vertex AI (via `GOOGLE_GENAI_USE_VERTEXAI=TRUE`)
- **Model**: Gemini 2.0 Flash
- **Streaming Mode**: NONE (synchronous responses)  
- **Artifact Saving**: Enabled for input blobs
- **Max LLM Calls**: 500 per session
- **Port**: 8001 (configurable in main.py)
- **Frontend**: Included static web interface

## Troubleshooting

### Server Won't Start
- Check if port 8001 is available
- Ensure virtual environment is activated
- Verify all dependencies are installed

### Agent Calls Fail
- Verify `GOOGLE_CLOUD_PROJECT` is set correctly
- Check `gcloud auth application-default login` is completed
- Ensure Vertex AI API is enabled in your project
- Verify internet connectivity and project billing

### Import Errors
- Make sure you're running from the quiz directory
- Verify the virtual environment is activated
- Check that all ADK dependencies are installed

## Development

To modify the server:

1. Edit `main.py` for API endpoints
2. Edit `agent.py` for agent configuration
3. Modify sub-agents in `subagents/` directory
4. Use `./start_server.sh` for testing

The server runs with auto-reload enabled, so changes to Python files will automatically restart the server.