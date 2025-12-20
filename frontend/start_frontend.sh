#!/bin/bash

# Auto Semantic Project - Frontend Startup Script

echo "🎨 Starting Frontend Server..."
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
    echo "✅ Dependencies installed."
fi

# Start the development server
echo ""
echo "✨ Starting Next.js development server on http://localhost:3000"
echo ""
npm run dev



