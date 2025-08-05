#!/usr/bin/env python3
"""
FastAPI interface for the Vresc Trading Intelligence System.

This application provides a web API for interacting with Vresc,
replacing the ADK web interface with a custom FastAPI implementation.
"""

from __future__ import annotations
import uuid
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from google.adk.runners import Runner
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.sessions.session import Session
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.events.event import Event
from google.genai import types

from agent import root_agent

def format_response_for_web(text: str) -> str:
    """Format agent response for better web display."""
    
    # Handle quiz question format
    if "Question:" in text and "Options:" in text:
        lines = text.split('\n')
        formatted_lines = []
        in_options = False
        option_labels = ['a)', 'b)', 'c)', 'd)', 'e)', 'f)']
        option_count = 0
        
        # Check if this is a True/False or Yes/No question
        text_lower = text.lower()
        is_binary_question = (
            ('true' in text_lower and 'false' in text_lower) or
            ('yes' in text_lower and 'no' in text_lower)
        )
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append("")
                continue
                
            if line == "Options:":
                formatted_lines.append("\n**Options:**")
                in_options = True
                option_count = 0
                continue
                
            if in_options and line.startswith('-'):
                option_text = line[1:].strip()
                # Don't add letters - agent already provides proper formatting
                formatted_lines.append(f"• {option_text}")
            elif line.startswith("Question:"):
                # Make question bold
                formatted_lines.append(f"**{line}**")
            else:
                formatted_lines.append(line)
                
        return '\n'.join(formatted_lines)
    
    # Handle market commentary format
    elif "Trading Markets Data" in text or "NEWS SUMMARY" in text or "FINANCE MARKETS" in text:
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append("")
                continue
                
            # Format headers
            if line.startswith("📰 NEWS SUMMARY") or line.startswith("📈 FINANCE MARKETS"):
                formatted_lines.append(f"\n**{line}**\n")
            elif line.startswith("---"):
                formatted_lines.append(f"\n**{line.replace('---', '').strip()}**")
            elif line.startswith("-"):
                # Format bullet points
                formatted_lines.append(f"• {line[1:].strip()}")
            elif ":" in line and not line.startswith("http"):
                # Format key-value pairs
                parts = line.split(":", 1)
                if len(parts) == 2:
                    formatted_lines.append(f"**{parts[0].strip()}:** {parts[1].strip()}")
                else:
                    formatted_lines.append(line)
            else:
                formatted_lines.append(line)
                
        return '\n'.join(formatted_lines)
    
    # Handle quiz feedback and other responses
    else:
        # Convert multiple spaces to single spaces but preserve line breaks
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Make quiz feedback bold (Correct!, Incorrect!, etc.)
                if any(word in line.lower() for word in ['correct!', 'incorrect!', 'nice,', 'well done']):
                    formatted_lines.append(f"**{line}**")
                # Make text that looks like headers bold
                elif line.endswith(':') and len(line) < 50:
                    formatted_lines.append(f"**{line}**")
                else:
                    formatted_lines.append(line)
            else:
                formatted_lines.append("")
                
        return '\n'.join(formatted_lines)

# Initialize services
session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()
memory_service = InMemoryMemoryService()

# Create the runner
runner = Runner(
    app_name="vresc-app",
    agent=root_agent,
    session_service=session_service,
    artifact_service=artifact_service,
    memory_service=memory_service
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    print("◈ Vresc Trading Intelligence System starting up...")
    print(f"◇ Agent: {root_agent.name}")
    print(f"◆ Runner configured with app name: {runner.app_name}")
    yield
    # Shutdown
    print("◈ Vresc Trading Intelligence System shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Vresc Trading Intelligence API",
    description="FastAPI interface for the Vresc Trading Intelligence System",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Request/Response Models
class ChatRequest(BaseModel):
    """Request model for chat interactions."""
    message: str = Field(..., description="User message to send to the agent")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")


class ChatResponse(BaseModel):
    """Response model for chat interactions."""
    response: str = Field(..., description="Agent's response")
    session_id: str = Field(..., description="Session ID for this conversation")
    artifacts: list[str] = Field(default_factory=list, description="List of artifact IDs created during this interaction")


class SessionInfo(BaseModel):
    """Model for session information."""
    session_id: str
    created_at: str
    last_update_time: str
    state: dict
    event_count: int


class SessionListResponse(BaseModel):
    """Response model for listing sessions."""
    sessions: list[SessionInfo]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    agent_name: str
    services: dict[str, str]


# API Endpoints

@app.get("/")
async def root():
    """Serve the main frontend interface."""
    return FileResponse("static/index.html")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        agent_name=root_agent.name,
        services={
            "session_service": "InMemorySessionService",
            "artifact_service": "InMemoryArtifactService"
        }
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Chat with Vresc Trading Intelligence.
    
    If no session_id is provided, a new session will be created.
    If a session_id is provided, the conversation will continue in that session.
    """
    try:
        user_id = "user1"
        
        # Get or create session
        if request.session_id:
            try:
                session = await session_service.get_session(
                    app_name="vresc-app",
                    user_id=user_id,
                    session_id=request.session_id
                )
            except Exception:
                # Session not found, create a new one
                session = await session_service.create_session(
                    app_name="vresc-app",
                    user_id=user_id,
                    session_id=request.session_id
                )
        else:
            # Create new session
            session = await session_service.create_session(
                app_name="vresc-app",
                user_id=user_id
            )

        # Create user message content
        user_message = types.Content(
            parts=[types.Part(text=request.message)],
            role="user"
        )

        # Run the agent and collect events
        events = []
        run_config = RunConfig(
            streaming_mode=StreamingMode.NONE,
            save_input_blobs_as_artifacts=True,
            max_llm_calls=500
        )
        
        # Log current session state before running
        print(f"\n=== SESSION STATE BEFORE RUN ===")
        print(f"Session ID: {session.id}")
        if session.state:
            print(f"Current state keys: {list(session.state.keys())}")
            for key, value in session.state.items():
                print(f"  {key}: {value}")
        else:
            print("Session state is empty")
        print("=== END SESSION STATE ===\n")
        
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=user_message,
            run_config=run_config
        ):
            events.append(event)

        # Log session state after running
        print(f"\n=== SESSION STATE AFTER RUN ===")
        print(f"Session ID: {session.id}")
        # Refresh session to get updated state
        updated_session = await session_service.get_session(
            app_name="vresc-app", user_id=user_id, session_id=session.id
        )
        if updated_session and updated_session.state:
            print(f"Updated state keys: {list(updated_session.state.keys())}")
            for key, value in updated_session.state.items():
                print(f"  {key}: {value}")
        else:
            print("Session state is still empty")
        print("=== END SESSION STATE ===\n")

        # Extract ALL meaningful responses (like ADK Web does)
        response_parts = []
        artifacts = []
        
        # Debug: Print all events to understand the flow  
        print(f"\n=== DEBUG: Total events generated: {len(events)} ===")
        for i, event in enumerate(events):
            author = event.author or "unknown"
            content_preview = ""
            try:
                if event.content and hasattr(event.content, 'parts'):
                    parts = getattr(event.content, 'parts', None)
                    if parts:
                        try:
                            for part in parts:
                                if part and hasattr(part, 'text') and part.text:
                                    content_preview = part.text[:100] + "..." if len(part.text) > 100 else part.text
                                    break
                        except (TypeError, AttributeError) as parts_error:
                            content_preview = f"Error iterating parts: {parts_error}"
            except Exception as e:
                content_preview = f"Error reading content: {e}"
            print(f"Event {i}: Author={author}, Content={repr(content_preview)}")
        print("=== END DEBUG ===\n")
        
        # Collect ALL meaningful text responses (following ADK Web pattern)
        for event in events:
            try:
                # Skip user events and events without content
                if event.author == "user" or not event.content:
                    continue
                
                # Multiple layers of null checking for robustness
                if not hasattr(event.content, 'parts'):
                    continue
                    
                # Get parts with additional null check
                parts = getattr(event.content, 'parts', None)
                if not parts:
                    continue
                
                # Look for text content that appears to be a user-facing response
                try:
                    for part in parts:
                        if not part:  # Skip None parts
                            continue
                        if hasattr(part, 'text') and part.text and part.text.strip():
                            text = part.text.strip()
                            print(f"DEBUG: Considering text: {repr(text[:200])}")
                            # Skip only JSON status messages and very short responses
                            # But allow quiz feedback and meaningful content
                            if (len(text) > 10 and 
                                not text.startswith('{"status"') and 
                                not (text.startswith('{"') and text.endswith('"}')) and
                                not text == "success"):
                                # Format the response for better web display
                                try:
                                    formatted_text = format_response_for_web(text)
                                except Exception as format_error:
                                    print(f"DEBUG: Error formatting text: {format_error}")
                                    formatted_text = text  # Use original text if formatting fails
                                response_parts.append(formatted_text)
                                print(f"DEBUG: Added response part: {repr(formatted_text[:200])}")
                                break
                except (TypeError, AttributeError) as parts_error:
                    print(f"DEBUG: Error iterating parts: {parts_error}")
                    continue
            except Exception as e:
                print(f"DEBUG: Error processing event {event}: {e}")
                continue
        
        # Join all meaningful responses with proper separation
        if response_parts:
            response_text = "\n\n---\n\n".join(response_parts)
        else:
            response_text = "No response generated."

        return ChatResponse(
            response=response_text,
            session_id=session.id,
            artifacts=artifacts
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")


@app.get("/sessions", response_model=SessionListResponse)
async def list_sessions():
    """List all active sessions."""
    try:
        sessions_data = []
        app_name = "vresc-app"
        user_id = "user1"
        
        # Access the internal sessions structure to list all sessions
        if app_name in session_service.sessions and user_id in session_service.sessions[app_name]:
            for session_id, session in session_service.sessions[app_name][user_id].items():
                # Get events for this session (simplified since we don't have event service)
                sessions_data.append(SessionInfo(
                    session_id=session.id,
                    created_at=session.created_at.isoformat(),
                    last_update_time=session.last_update_time.isoformat(),
                    state=session.state,
                    event_count=len(session.conversation_history)
                ))
        
        return SessionListResponse(sessions=sessions_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")


@app.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session_info(session_id: str):
    """Get information about a specific session."""
    try:
        session = await session_service.get_session(
            app_name="vresc-app",
            user_id="user1",
            session_id=session_id
        )
        
        return SessionInfo(
            session_id=session.id,
            created_at=session.created_at.isoformat(),
            last_update_time=session.last_update_time.isoformat(),
            state=session.state,
            event_count=len(session.conversation_history)
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Session not found")


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a specific session."""
    try:
        await session_service.delete_session(
            app_name="vresc-app",
            user_id="user1",
            session_id=session_id
        )
        return {"message": f"Session {session_id} deleted successfully"}
    except Exception:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/artifacts/{session_id}/{filename}")
async def get_artifact(session_id: str, filename: str, version: Optional[int] = None):
    """Get a specific artifact by session ID and filename."""
    try:
        artifact_part = await artifact_service.load_artifact(
            app_name="vresc-app",
            user_id="user1",
            session_id=session_id,
            filename=filename,
            version=version
        )
        
        if not artifact_part:
            raise HTTPException(status_code=404, detail="Artifact not found")
        
        return {
            "session_id": session_id,
            "filename": filename,
            "version": version,
            "mime_type": getattr(artifact_part, 'mime_type', 'application/octet-stream'),
            "size": len(artifact_part.data) if hasattr(artifact_part, 'data') and artifact_part.data else 0
        }
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Artifact not found")
        raise HTTPException(status_code=500, detail=f"Error retrieving artifact: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )