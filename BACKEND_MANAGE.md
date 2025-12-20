# Backend Management Commands

Use these commands to manually control the backend server.

## 1. Start the Backend
```bash
# Move to backend directory and activate venv
cd backend
source venv/bin/activate

# SAFE START (Ignores any old OpenAI keys in your terminal)
unset OPENAI_API_KEY && uvicorn sql_agent:app --host 0.0.0.0 --port 8000

# Standard start in foreground
uvicorn sql_agent:app --host 0.0.0.0 --port 8000


# Start server in background (continues after closing terminal)
nohup uvicorn sql_agent:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
```

## 2. Check if Backend is Running
```bash
# Check if port 8000 is listening
lsof -i :8000

# Alternative check
ps aux | grep uvicorn
```

## 3. Kill the Backend (Stop)
```bash
# Kill by port number (Quickest way)
fuser -k 8000/tcp

# Kill by process name
pkill -9 -f uvicorn
```

## 4. View Logs
```bash
# See the last 50 lines of the log
tail -n 50 /tmp/backend.log

# Follow logs in real-time
tail -f /tmp/backend.log
```

## 5. Health Check
```bash
# Check if API is responding and see which AI is active
curl http://localhost:8000/health
```

