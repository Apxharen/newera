import os

import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app


# Get the directory where main.py is located (this should contain agent subdirectories)
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Example allowed origins for CORS
ALLOWED_ORIGINS = ["http://localhost:8080", "*"]
# Set web=True if you intend to serve a web interface, False otherwise
SERVE_WEB_INTERFACE = True
# Session service URI (SQLite database)
SESSION_SERVICE_URI = "sqlite:///./sessions.db"


# Call the function to get the FastAPI app instance
# The agent directory (vresc) should contain __init__.py and agent.py files
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    session_service_uri=SESSION_SERVICE_URI,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
)

# Add redirect from root to the development UI
from fastapi.responses import RedirectResponse

@app.get("/")
async def root():
    """Redirect root to the development UI"""
    return RedirectResponse(url="/dev-ui/", status_code=307)

if __name__ == "__main__":
    # Use the PORT environment variable provided by Cloud Run, defaulting to 8080
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))