#!/bin/bash

# Setup and Test Script for Report Management Feature
# This script will:
# 1. Check prerequisites
# 2. Apply database migration
# 3. Start the backend server
# 4. Test all endpoints

set -e  # Exit on error

echo "🚀 Auto-Semantic BI Platform - Setup & Test"
echo "==========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# =============================================================================
# 1. CHECK PREREQUISITES
# =============================================================================
echo "📋 Step 1: Checking Prerequisites..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo "   Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo "   Activating virtual environment..."
source venv/bin/activate

# Check if required packages are installed
echo "   Checking Python packages..."
pip install -q -r requirements.txt
echo -e "${GREEN}✅ All packages installed${NC}"

# Check if PostgreSQL is accessible
echo ""
echo "🗄️  Step 2: Checking Database Connection..."

# Prompt for database URL if not set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}⚠️  DATABASE_URL not set${NC}"
    echo ""
    echo "Please provide your database connection details:"
    read -p "Host (default: localhost): " DB_HOST
    DB_HOST=${DB_HOST:-localhost}
    
    read -p "Port (default: 5432): " DB_PORT
    DB_PORT=${DB_PORT:-5432}
    
    read -p "Database name (default: analytics): " DB_NAME
    DB_NAME=${DB_NAME:-analytics}
    
    read -p "Username (default: postgres): " DB_USER
    DB_USER=${DB_USER:-postgres}
    
    read -sp "Password (default: postgres): " DB_PASS
    DB_PASS=${DB_PASS:-postgres}
    echo ""
    
    export DATABASE_URL="postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
fi

echo "   Testing database connection..."
if psql "$DATABASE_URL" -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Database connection successful${NC}"
else
    echo -e "${RED}❌ Cannot connect to database${NC}"
    echo "   Connection string: $DATABASE_URL"
    echo ""
    echo "   Troubleshooting:"
    echo "   1. Make sure PostgreSQL is running"
    echo "   2. Check connection details"
    echo "   3. Try: docker ps | grep postgres"
    exit 1
fi

# =============================================================================
# 2. APPLY DATABASE MIGRATION
# =============================================================================
echo ""
echo "📊 Step 3: Applying Database Migration..."

# Check if schema already exists
if psql "$DATABASE_URL" -c "SELECT 1 FROM information_schema.schemata WHERE schema_name = 'analytics_llm'" | grep -q 1; then
    echo -e "${YELLOW}⚠️  Schema 'analytics_llm' already exists${NC}"
    read -p "   Do you want to recreate it? (y/N): " RECREATE
    
    if [[ $RECREATE =~ ^[Yy]$ ]]; then
        echo "   Dropping existing schema..."
        psql "$DATABASE_URL" -c "DROP SCHEMA IF EXISTS analytics_llm CASCADE;" > /dev/null
        echo "   Applying migration..."
        psql "$DATABASE_URL" -f migrations/001_create_reports_schema.sql > /dev/null
        echo -e "${GREEN}✅ Migration applied (recreated)${NC}"
    else
        echo "   Skipping migration (using existing schema)"
    fi
else
    echo "   Applying migration..."
    psql "$DATABASE_URL" -f migrations/001_create_reports_schema.sql > /dev/null
    echo -e "${GREEN}✅ Migration applied successfully${NC}"
fi

# Verify tables were created
TABLE_COUNT=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'analytics_llm';")
echo "   Created $TABLE_COUNT tables in analytics_llm schema"

# =============================================================================
# 3. CHECK API KEY
# =============================================================================
echo ""
echo "🔑 Step 4: Checking AI API Configuration..."

if [ -z "$OPENAI_API_KEY" ] && [ -z "$GROQ_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  No AI API key found${NC}"
    echo ""
    echo "You need either OpenAI or Groq API key to use the /ask endpoint."
    echo "Report management endpoints will work without it."
    echo ""
    read -p "Enter OpenAI API key (or press Enter to skip): " API_KEY
    
    if [ ! -z "$API_KEY" ]; then
        export OPENAI_API_KEY="$API_KEY"
        export OPENAI_MODEL="gpt-4o-mini"
        echo -e "${GREEN}✅ API key configured${NC}"
    else
        echo "   Skipping AI configuration (report endpoints will still work)"
    fi
else
    echo -e "${GREEN}✅ API key found${NC}"
fi

# Set semantic JSON path
export SEMANTIC_JSON="backend/metadata/semantic.json"

# =============================================================================
# 4. START SERVER
# =============================================================================
echo ""
echo "🚀 Step 5: Starting Backend Server..."
echo ""
echo -e "${GREEN}Server will start at: http://localhost:8000${NC}"
echo -e "${GREEN}API Documentation at: http://localhost:8000/docs${NC}"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "==========================================="

# Start server
uvicorn sql_agent:app --reload --host 0.0.0.0 --port 8000

