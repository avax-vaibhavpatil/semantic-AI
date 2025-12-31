# 🧪 Testing Guide - Report Management Feature

Complete guide to test your new report management backend!

---

## 🚀 **Quick Start (3 Steps)**

### **Step 1: Setup & Start Server**

```bash
cd /home/avaxpro16/Desktop/trial/auto_semantic_project/backend

# Run the setup script (interactive)
./setup_and_test.sh
```

This script will:
- ✅ Check prerequisites
- ✅ Apply database migration
- ✅ Start the backend server at `http://localhost:8000`

### **Step 2: Test API Endpoints**

Open a **new terminal** and run:

```bash
cd /home/avaxpro16/Desktop/trial/auto_semantic_project/backend
source venv/bin/activate

# Run automated tests
python test_endpoints.py
```

This will test all 10 endpoints automatically!

### **Step 3: Explore Interactive Docs**

Open in your browser:
```
http://localhost:8000/docs
```

Click any endpoint → "Try it out" → Fill form → Execute!

---

## 📋 **Manual Setup (If Script Doesn't Work)**

### **1. Set Environment Variables**

```bash
# Database connection
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/analytics"

# AI API (optional for /ask endpoint)
export OPENAI_API_KEY="your-key-here"
export OPENAI_MODEL="gpt-4o-mini"

# Semantic layer
export SEMANTIC_JSON="backend/metadata/semantic.json"
```

### **2. Apply Database Migration**

```bash
cd /home/avaxpro16/Desktop/trial/auto_semantic_project/backend

# Apply migration
psql $DATABASE_URL -f migrations/001_create_reports_schema.sql
```

### **3. Start Server**

```bash
# Activate virtual environment
source venv/bin/activate

# Start server
uvicorn sql_agent:app --reload --host 0.0.0.0 --port 8000
```

---

## 🧪 **Testing Methods**

### **Method 1: Automated Test Script** ⭐ (Recommended)

```bash
python test_endpoints.py
```

**What it tests:**
1. ✅ Health check
2. ✅ Save report
3. ✅ List reports
4. ✅ Get single report
5. ✅ Execute report
6. ✅ Update report
7. ✅ Search reports
8. ✅ Execution history
9. ✅ Filter by favorites
10. ✅ Delete report

### **Method 2: Interactive API Docs** ⭐ (Best for Exploration)

1. Open `http://localhost:8000/docs`
2. Click any endpoint
3. Click "Try it out"
4. Fill in the form
5. Click "Execute"
6. See results!

### **Method 3: cURL Commands**

```bash
# Save a report
curl -X POST http://localhost:8000/reports/save \
  -H "Content-Type: application/json" \
  -d '{
    "report_name": "My Test Report",
    "user_question": "Show top customers",
    "generated_sql": "SELECT * FROM public.gwanalytics LIMIT 10",
    "tags": ["test"]
  }'

# List reports
curl http://localhost:8000/reports

# Execute report (replace 1 with your report_id)
curl -X POST http://localhost:8000/reports/1/execute

# Mark as favorite
curl -X PATCH http://localhost:8000/reports/1 \
  -H "Content-Type: application/json" \
  -d '{"is_favorite": true}'

# Delete report
curl -X DELETE http://localhost:8000/reports/1
```

### **Method 4: Python Script**

```python
import requests

BASE_URL = "http://localhost:8000"

# Save report
response = requests.post(
    f"{BASE_URL}/reports/save",
    json={
        "report_name": "Python Test Report",
        "user_question": "Show data",
        "generated_sql": "SELECT 1"
    }
)
print(response.json())
# Output: {"report_id": 1, "message": "Report saved successfully"}

# List reports
response = requests.get(f"{BASE_URL}/reports")
print(response.json())

# Execute report
report_id = 1
response = requests.post(f"{BASE_URL}/reports/{report_id}/execute")
data = response.json()
print(f"Got {data['row_count']} rows in {data['execution_time_ms']}ms")
```

---

## ✅ **Expected Results**

### **1. Successful Migration**

```sql
Created 2 tables in analytics_llm schema:
- saved_reports
- report_executions
```

### **2. Server Started**

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### **3. Test Results**

```
🧪 Report Management API Test Suite
============================================================

Test 1: Health Check
✅ GET /health - Status 200
   Semantic loaded: True

Test 2: Save a Report
✅ POST /reports/save - Status 200
   Report ID: 1
   Message: Report saved successfully

Test 3: List All Reports
✅ GET /reports?limit=10 - Status 200
   Total reports: 3
   Fetched: 3 reports

[... more tests ...]

✅ All tests completed!
```

---

## 🐛 **Troubleshooting**

### **Problem: Cannot connect to database**

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Or for system PostgreSQL
sudo systemctl status postgresql

# Test connection manually
psql "postgresql://postgres:postgres@localhost:5432/analytics" -c "SELECT 1"
```

**Solution:**
- Make sure PostgreSQL is running
- Check DATABASE_URL is correct
- Verify credentials

### **Problem: Port 8000 already in use**

```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use a different port
uvicorn sql_agent:app --reload --port 8001
```

### **Problem: Module not found**

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### **Problem: Migration fails**

```bash
# Check if schema already exists
psql $DATABASE_URL -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'analytics_llm';"

# Drop and recreate (WARNING: deletes data!)
psql $DATABASE_URL -c "DROP SCHEMA IF EXISTS analytics_llm CASCADE;"
psql $DATABASE_URL -f migrations/001_create_reports_schema.sql
```

### **Problem: Import errors in Python**

```bash
# Make sure you're in the backend directory
cd /home/avaxpro16/Desktop/trial/auto_semantic_project/backend

# Python needs to find the modules
export PYTHONPATH=/home/avaxpro16/Desktop/trial/auto_semantic_project/backend:$PYTHONPATH

# Or run from backend directory
cd backend && uvicorn sql_agent:app --reload
```

---

## 📊 **Verifying Database**

Check that everything was created properly:

```sql
-- Connect to database
psql $DATABASE_URL

-- List schemas
\dn

-- Should see: analytics_llm

-- List tables
\dt analytics_llm.*

-- Should see:
--  analytics_llm | saved_reports
--  analytics_llm | report_executions

-- Check sample data
SELECT report_id, report_name FROM analytics_llm.saved_reports;

-- Should see 3 sample reports

-- Check indexes
\di analytics_llm.*

-- Should see 4+ indexes
```

---

## 🎯 **What to Test**

### **Basic CRUD Operations:**
- ✅ Create: Save a report
- ✅ Read: List reports, get single report
- ✅ Update: Mark as favorite, rename
- ✅ Delete: Soft delete a report

### **Advanced Features:**
- ✅ Execute report with fresh data
- ✅ Pagination (limit/offset)
- ✅ Search by name
- ✅ Filter by tags
- ✅ Filter by favorite status
- ✅ Execution history tracking

### **Security:**
- ✅ User isolation (users can only see their own reports)
- ✅ SQL injection prevention
- ✅ Input validation

### **Performance:**
- ✅ Query execution time tracking
- ✅ Indexed queries (fast even with many reports)
- ✅ Pagination (doesn't load all data at once)

---

## 📈 **Success Metrics**

Your backend is working correctly if:

1. ✅ All endpoints return expected status codes
2. ✅ Reports can be saved and retrieved
3. ✅ Execute endpoint returns fresh data
4. ✅ Search and filtering work
5. ✅ No SQL errors in logs
6. ✅ Response times < 200ms (except execute)
7. ✅ Interactive docs show all endpoints
8. ✅ Test script passes all tests

---

## 🎉 **Next Steps**

Once testing is successful:

1. **Frontend Development**
   - Build save report button
   - Create saved reports list page
   - Add search and filter UI

2. **Authentication**
   - Replace `demo_user` with real user system
   - Add JWT token validation
   - Implement proper login

3. **Production Deployment**
   - Set up proper environment variables
   - Configure HTTPS
   - Add monitoring
   - Set up database backups

---

## 📞 **Need Help?**

Check logs:
```bash
# Server logs show in terminal where uvicorn is running
# Look for ERROR or WARNING messages
```

Enable debug mode:
```python
# In sql_agent.py, temporarily add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

**Created:** 2025-12-15  
**Backend Version:** 1.0.0  
**Endpoints:** 8 working endpoints + /health + /ask (original)

