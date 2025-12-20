# 🔑 API Key Setup Guide

## ❓ **Why You're Getting the Error**

The error you're seeing:
```
AI model error: Error code: 401 - invalid_api_key
```

**Cause:** The backend is using a dummy API key (`sk-dummy-key-for-testing`)

**Important:** The **Saved Reports feature works WITHOUT any API key!**

Only the `/ask` endpoint (AI query generation) needs an API key.

---

## 🎯 **Two Options**

### **Option 1: Use Saved Reports Only** (No API Key Needed!)

**What works:**
- ✅ Save reports
- ✅ Execute saved reports  
- ✅ Search reports
- ✅ Delete reports
- ✅ Mark favorites
- ✅ All report management features

**What doesn't work:**
- ❌ AI natural language query generation (`/ask` endpoint)

**If this is enough for you:** You're done! Just ignore the API key error.

---

### **Option 2: Enable AI Query Generation** (Needs API Key)

If you want to use the `/ask` endpoint to generate SQL from natural language:

#### **Step 1: Get Your Groq API Key**

1. Go to: https://console.groq.com/keys
2. Sign up or log in
3. Click "Create API Key"
4. Copy your key (starts with `gsk_...`)

#### **Step 2: Restart Backend with Your Key**

**Method A: Interactive Script** (Easiest)

```bash
cd /home/avaxpro16/Desktop/trial/auto_semantic_project/backend
./start_with_groq.sh
```

When prompted, paste your Groq API key.

**Method B: Manual Setup**

```bash
cd /home/avaxpro16/Desktop/trial/auto_semantic_project/backend

# Stop existing backend
pkill -f "uvicorn sql_agent:app"

# Set environment variables
export DATABASE_URL="postgresql://postgres:root@localhost:5430/analytics-llm"
export SEMANTIC_JSON="metadata/semantic.json"
export GROQ_API_KEY="your-groq-key-here"  # ← Your actual key
export GROQ_MODEL="mixtral-8x7b-32768"

# Start server
source venv/bin/activate
uvicorn sql_agent:app --reload --host 0.0.0.0 --port 8000
```

**Method C: Edit the Script** (Permanent)

Edit `start_with_groq.sh` and replace:
```bash
read -p "Groq API Key: " GROQ_KEY
```

With:
```bash
GROQ_KEY="your-actual-groq-key-here"
```

Then run:
```bash
./start_with_groq.sh
```

---

## 🧪 **Testing**

### **Test Saved Reports (No API Key Needed)**

```bash
# 1. Save a report
curl -X POST http://localhost:8000/reports/save \
  -H "Content-Type: application/json" \
  -d '{
    "report_name": "Test Report",
    "user_question": "Show data",
    "generated_sql": "SELECT * FROM public.gwanalytics LIMIT 5"
  }'

# 2. List reports
curl http://localhost:8000/reports

# 3. Execute report (get fresh data)
curl -X POST http://localhost:8000/reports/1/execute
```

**This works without any API key!** ✅

### **Test AI Query Generation (Needs API Key)**

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me top 5 customers",
    "max_rows": 5
  }'
```

**This requires a valid Groq or OpenAI API key.** 🔑

---

## 🎨 **Using the Frontend**

### **Without API Key:**

You can still:
1. ✅ Open the sidebar
2. ✅ View saved reports
3. ✅ Execute saved reports
4. ✅ See fresh data
5. ✅ Save reports (if you have SQL)
6. ❌ Can't use the "Ask" feature (needs AI)

### **With API Key:**

Everything works:
1. ✅ Ask questions in natural language
2. ✅ AI generates SQL
3. ✅ Save the results
4. ✅ Execute later
5. ✅ All features enabled

---

## 🔄 **Quick Restart**

If you need to restart the backend:

```bash
# Stop
pkill -f "uvicorn sql_agent:app"

# Start with Groq key
cd backend
./start_with_groq.sh
```

---

## 📊 **What Works Where**

| Feature | No API Key | With API Key |
|---------|-----------|--------------|
| **Save Report** | ✅ | ✅ |
| **Execute Report** | ✅ | ✅ |
| **List Reports** | ✅ | ✅ |
| **Search Reports** | ✅ | ✅ |
| **Delete Reports** | ✅ | ✅ |
| **Favorites** | ✅ | ✅ |
| **AI Query Gen (/ask)** | ❌ | ✅ |

---

## 💡 **Recommendation**

**For Testing Saved Reports Feature:**
- No API key needed
- Just use the saved reports sidebar
- All management features work

**For Full Experience:**
- Get a free Groq API key (https://console.groq.com)
- Use `./start_with_groq.sh`
- Everything works!

---

## 🐛 **Troubleshooting**

### **Error: "invalid_api_key"**

**Solution:** This only affects `/ask` endpoint. Saved reports still work!

Or set a real API key using the script above.

### **Error: "Could not load semantic JSON"**

**Solution:** The SEMANTIC_JSON path is set correctly in the script.
Just run: `./start_with_groq.sh`

### **Multiple backend processes running**

```bash
# Kill all
pkill -f "uvicorn sql_agent:app"

# Start fresh
./start_with_groq.sh
```

### **Port 8000 already in use**

```bash
# Find and kill process
lsof -ti :8000 | xargs kill -9

# Start again
./start_with_groq.sh
```

---

## 🎯 **Current Status**

Your setup RIGHT NOW:
- ✅ Backend running on port 8000
- ✅ Frontend running on port 3000
- ✅ Database connected
- ✅ **Saved reports feature FULLY WORKING**
- ⚠️  AI query generation disabled (needs key)

**To use saved reports: Just open http://localhost:3000 and click the menu button!**

---

## 📞 **Quick Commands**

```bash
# Check if backend is running
curl http://localhost:8000/health

# Check saved reports (no key needed)
curl http://localhost:8000/reports

# Restart with Groq key
cd backend && ./start_with_groq.sh

# View logs
tail -f /tmp/backend.log
```

---

**Bottom Line:** Your saved reports feature is working perfectly right now! The API key is only needed if you want AI to generate SQL queries for you. 🎉

