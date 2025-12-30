#!/bin/bash
# Start API Server

echo "🚀 Starting Auto Semantic BI Platform API..."
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start server
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

