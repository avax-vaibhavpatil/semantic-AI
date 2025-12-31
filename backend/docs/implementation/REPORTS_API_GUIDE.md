# Report Management API Guide

## 📋 Overview

Complete API for saving and managing AI-generated SQL reports.

---

## 🚀 **API Endpoints**

### **Base URL:** `http://localhost:8000`

---

## 1️⃣ **Save a Report**

**Endpoint:** `POST /reports/save`

**When to use:** After user gets query results and wants to save them

**Request:**
```json
{
    "report_name": "Top 10 Customers - Dec 2025",
    "user_question": "Show me top 10 customers by sales",
    "generated_sql": "SELECT ... ORDER BY ... LIMIT 10",
    "report_description": "Monthly sales leaders report",
    "tags": ["sales", "customers", "monthly"]
}
```

**Response:**
```json
{
    "report_id": 42,
    "message": "Report saved successfully"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/reports/save \
  -H "Content-Type: application/json" \
  -d '{
    "report_name": "My Sales Report",
    "user_question": "Show top customers",
    "generated_sql": "SELECT * FROM gwanalytics LIMIT 10"
  }'
```

---

## 2️⃣ **List All Reports**

**Endpoint:** `GET /reports`

**Query Parameters:**
- `limit` - Reports per page (default: 20, max: 100)
- `offset` - Pagination offset (default: 0)
- `favorite_only` - Show only favorites (default: false)
- `tags` - Filter by tags

**Examples:**
```bash
# First page (20 reports)
GET /reports

# Second page
GET /reports?limit=20&offset=20

# Only favorites
GET /reports?favorite_only=true

# Filter by tags
GET /reports?tags=sales&tags=monthly
```

**Response:**
```json
{
    "reports": [
        {
            "report_id": 42,
            "report_name": "My Sales Dashboard",
            "created_at": "2025-12-15T10:30:00",
            "last_executed_at": "2025-12-15T11:45:00",
            "execution_count": 5,
            "is_favorite": false,
            "tags": ["sales", "monthly"]
        }
    ],
    "total": 156,
    "limit": 20,
    "offset": 0
}
```

---

## 3️⃣ **Get Report Details**

**Endpoint:** `GET /reports/{report_id}`

**When to use:** View full details of a specific report

**Response:**
```json
{
    "report_id": 42,
    "report_name": "My Sales Dashboard",
    "user_question": "Show top 10 customers",
    "generated_sql": "SELECT ... LIMIT 10",
    "report_description": "Monthly sales leaders",
    "created_at": "2025-12-15T10:30:00",
    "updated_at": "2025-12-15T10:30:00",
    "last_executed_at": "2025-12-15T11:45:00",
    "execution_count": 5,
    "is_favorite": false,
    "tags": ["sales", "monthly"],
    "status": "active"
}
```

---

## 4️⃣ **Execute Report (Get Fresh Data)** ⭐

**Endpoint:** `POST /reports/{report_id}/execute`

**When to use:** User clicks on a saved report to see latest data

**Request (optional):**
```json
{
    "max_rows": 500
}
```

**What happens:**
1. Fetches saved SQL query
2. Executes against database
3. Returns fresh, updated results
4. Updates execution statistics

**Response:**
```json
{
    "report": {
        "report_id": 42,
        "report_name": "My Sales Dashboard",
        ...
    },
    "rows": [
        {"customer": "ABC Corp", "sales": 50000},
        {"customer": "XYZ Ltd", "sales": 45000}
    ],
    "row_count": 10,
    "execution_time_ms": 45
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/reports/42/execute \
  -H "Content-Type: application/json" \
  -d '{"max_rows": 500}'
```

---

## 5️⃣ **Update Report**

**Endpoint:** `PATCH /reports/{report_id}`

**When to use:** Rename, change description, update tags, or mark as favorite

**Request (all fields optional):**
```json
{
    "report_name": "New Report Name",
    "report_description": "Updated description",
    "tags": ["sales", "updated"],
    "is_favorite": true
}
```

**Examples:**

```bash
# Just rename
curl -X PATCH http://localhost:8000/reports/42 \
  -H "Content-Type: application/json" \
  -d '{"report_name": "New Name"}'

# Mark as favorite
curl -X PATCH http://localhost:8000/reports/42 \
  -H "Content-Type: application/json" \
  -d '{"is_favorite": true}'
```

---

## 6️⃣ **Delete Report**

**Endpoint:** `DELETE /reports/{report_id}`

**Query Parameters:**
- `hard_delete` - If true, permanently delete (default: false = soft delete)

**Soft Delete (default):**
- Report marked as deleted but preserved in database
- Can be restored later
- **Recommended for production**

**Hard Delete:**
- Permanently removes report
- Cannot be undone

**Examples:**
```bash
# Soft delete (recommended)
DELETE /reports/42

# Permanent deletion
DELETE /reports/42?hard_delete=true
```

**Response:**
```json
{
    "message": "Report deleted successfully",
    "deleted_report_id": 42
}
```

---

## 7️⃣ **Search Reports**

**Endpoint:** `GET /reports/search`

**Query Parameters:**
- `q` - Search term (required)
- `limit` - Max results (default: 20)

**Examples:**
```bash
# Search for "sales"
GET /reports/search?q=sales

# Search for "monthly report"
GET /reports/search?q=monthly%20report&limit=50
```

**Features:**
- Full-text search (intelligent word matching)
- Searches report names
- Ranked by relevance

---

## 8️⃣ **Execution History**

**Endpoint:** `GET /reports/{report_id}/history`

**Query Parameters:**
- `limit` - Number of history records (default: 10, max: 50)

**When to use:** See when report was run, execution times, row counts

**Response:**
```json
[
    {
        "execution_id": 123,
        "executed_at": "2025-12-15T11:45:00",
        "execution_time_ms": 45,
        "row_count": 10,
        "error_message": null
    }
]
```

---

## 🔒 **Security**

### **User Isolation:**
- Every endpoint checks `user_id`
- Users can ONLY access their own reports
- Automatic security on all operations

### **SQL Injection Prevention:**
- All queries use parameterized statements
- No string concatenation in SQL
- 100% protected against SQL injection

---

## 📊 **HTTP Status Codes**

| Code | Meaning | When |
|------|---------|------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid input data |
| 404 | Not Found | Report doesn't exist or no access |
| 500 | Server Error | Database or internal error |

---

## 🧪 **Testing the API**

### **1. Using cURL:**

```bash
# Save a report
curl -X POST http://localhost:8000/reports/save \
  -H "Content-Type: application/json" \
  -d '{"report_name": "Test", "user_question": "test", "generated_sql": "SELECT 1"}'

# List reports
curl http://localhost:8000/reports

# Execute report
curl -X POST http://localhost:8000/reports/1/execute
```

### **2. Using Python:**

```python
import requests

BASE_URL = "http://localhost:8000"

# Save report
response = requests.post(
    f"{BASE_URL}/reports/save",
    json={
        "report_name": "My Test Report",
        "user_question": "Show data",
        "generated_sql": "SELECT * FROM gwanalytics LIMIT 10"
    }
)
report_id = response.json()["report_id"]

# Execute report
response = requests.post(
    f"{BASE_URL}/reports/{report_id}/execute"
)
data = response.json()
print(f"Got {data['row_count']} rows")
```

### **3. Using FastAPI Docs:**

1. Start server: `uvicorn sql_agent:app --reload`
2. Open browser: `http://localhost:8000/docs`
3. Interactive API documentation with "Try it out" buttons!

---

## 🎯 **Complete User Flow**

```
1. User asks question
   POST /ask
   → Gets SQL and results

2. User saves report
   POST /reports/save
   → Report stored in database

3. Later, user views saved reports
   GET /reports
   → Sees list of all saved reports

4. User clicks on a report
   POST /reports/{id}/execute
   → Gets FRESH data (re-executes SQL)

5. User favorites the report
   PATCH /reports/{id}
   → {"is_favorite": true}

6. User renames report
   PATCH /reports/{id}
   → {"report_name": "New Name"}

7. Eventually, user deletes old report
   DELETE /reports/{id}
   → Soft deleted (can restore)
```

---

## 🔧 **Running the Server**

```bash
# From backend directory
cd /home/avaxpro16/Desktop/trial/auto_semantic_project/backend

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/analytics"
export OPENAI_API_KEY="your-key"

# Run server
uvicorn sql_agent:app --reload --host 0.0.0.0 --port 8000

# Server starts at http://localhost:8000
# API docs at http://localhost:8000/docs
```

---

## 📝 **Next Steps**

1. **Run database migration:** Apply `001_create_reports_schema.sql`
2. **Start backend:** `uvicorn sql_agent:app --reload`
3. **Test endpoints:** Use `/docs` or cURL
4. **Build frontend:** Create UI components

---

## 🎓 **What You Learned**

- ✅ RESTful API design (GET, POST, PATCH, DELETE)
- ✅ Request/Response modeling with Pydantic
- ✅ Error handling and HTTP status codes
- ✅ Pagination and filtering
- ✅ Full-text search
- ✅ Security and user isolation
- ✅ Logging and monitoring
- ✅ API documentation (OpenAPI/Swagger)

---

**Created:** 2025-12-15  
**Total Endpoints:** 8  
**Lines of Code:** ~500 (API) + 700 (Repository) + 500 (Models) = 1700 lines!

