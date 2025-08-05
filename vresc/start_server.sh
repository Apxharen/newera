#!/bin/bash

# Vresc Trading Intelligence System Startup Script
# This script activates the virtual environment and starts the Vresc server

echo "◈ Starting Vresc Trading Intelligence System..."
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please create a virtual environment first:"
    echo "python -m venv .venv"
    echo "source .venv/bin/activate"
    echo "pip install -r ../requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Configure for Vertex AI
export GOOGLE_GENAI_USE_VERTEXAI=TRUE

# Set default location if not provided
if [ -z "$GOOGLE_CLOUD_LOCATION" ]; then
    export GOOGLE_CLOUD_LOCATION="us-central1"
fi

# Check if required environment variables are set for Vertex AI
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    echo ""
    echo "⚠️  Warning: GOOGLE_CLOUD_PROJECT not set!"
    echo ""
    echo "To use Vresc with Vertex AI, you need to:"
    echo "  1. Set your project: export GOOGLE_CLOUD_PROJECT='your-project-id'"
    echo "  2. Authenticate: gcloud auth application-default login"
    echo "  3. Enable Vertex AI API in your project"
    echo ""
    read -p "Press Enter to continue anyway (server will start but agent calls will fail)..."
fi

echo "🔧 Using Vertex AI (GOOGLE_GENAI_USE_VERTEXAI=TRUE)"
if [ ! -z "$GOOGLE_CLOUD_PROJECT" ]; then
    echo "📋 Project: $GOOGLE_CLOUD_PROJECT"
fi
if [ ! -z "$GOOGLE_CLOUD_LOCATION" ]; then
    echo "📍 Location: $GOOGLE_CLOUD_LOCATION"
fi

# Start the FastAPI server
echo ""
echo "🏃 Starting FastAPI server on http://localhost:8001"
echo "🌐 Web Interface: http://localhost:8001/"
echo "📊 Health check: http://localhost:8001/health"
echo "📝 API docs: http://localhost:8001/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python main.py