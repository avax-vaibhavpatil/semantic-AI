#!/bin/bash

# Startup script for backend with Groq API
# Save your Groq API key here or set it as environment variable

echo "🚀 Starting Backend Server with Groq API"
echo "========================================"
echo ""

# Kill any existing backend processes
echo "Stopping any existing backend processes..."
pkill -f "uvicorn sql_agent:app" 2>/dev/null
sleep 2

cd /home/avaxpro16/Desktop/trial/auto_semantic_project/backend

# Activate virtual environment
source venv/bin/activate

# Set database connection
export DATABASE_URL="postgresql://postgres:root@localhost:5430/analytics-llm"

# Set semantic JSON path (relative from backend directory)
export SEMANTIC_JSON="metadata/semantic.json"

# Set your Groq API key here!
# Get your key from: https://console.groq.com/keys
echo "📝 Please enter your Groq API key:"
echo "   (or press Ctrl+C and edit this script to hardcode it)"
read -p "Groq API Key: " GROQ_KEY

if [ -z "$GROQ_KEY" ]; then
    echo ""
    echo "❌ No API key provided!"
    echo ""
    echo "Option 1: Run this script and paste your key when prompted"
    echo "Option 2: Edit this script and set:"
    echo "          export GROQ_API_KEY=\"your-key-here\""
    echo ""
    echo "Option 3: Skip AI query generation (saved reports will still work):"
    echo "          Just press Enter to continue without API key"
    echo ""
    read -p "Continue without API key? (y/N): " CONTINUE
    
    if [[ ! $CONTINUE =~ ^[Yy]$ ]]; then
        echo "Exiting..."
        exit 1
    fi
    
    # Set dummy key to allow server to start
    export OPENAI_API_KEY="sk-dummy-key"
    echo ""
    echo "⚠️  Starting WITHOUT AI query generation"
    echo "   Saved reports feature will work!"
    echo "   /ask endpoint will NOT work"
    echo ""
else
    export GROQ_API_KEY="$GROQ_KEY"
    export GROQ_MODEL="mixtral-8x7b-32768"
    echo ""
    echo "✅ Groq API key configured"
    echo ""
fi

echo "✅ Database: $DATABASE_URL"
echo "✅ Semantic Layer: $SEMANTIC_JSON"
echo ""
echo "Starting server at http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================"
echo ""

# Start server
uvicorn sql_agent:app --reload --host 0.0.0.0 --port 8000

