# API Testing with curl - Complete Guide

This document contains all curl commands to test the Auto Semantic BI Platform API.

## Server Status

The API server should be running on: `http://localhost:8000`

To start the server:
```bash
cd backend
source venv/bin/activate
uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

Or use the startup script:
```bash
./start_api.sh
```

---

## Test Results Summary

✅ **All 11 tests passed!**

- ✅ Health Check
- ✅ Query Endpoint (Natural Language to SQL)
- ✅ Save Report
- ✅ Get Report by ID
- ✅ List User Reports
- ✅ Update Report
- ✅ Execute Saved Report
- ✅ Error Handling - Invalid Query
- ✅ Error Handling - Missing Field
- ✅ Error Handling - Non-existent Report
- ✅ Delete Report

---

## Individual curl Commands

### 1. Health Check

```bash
curl -X GET http://localhost:8000/health
```

**Expected Response:**
```json
{
    "status": "ok",
    "service": "Auto Semantic BI Platform",
    "version": "1.0.0"
}
```

---

### 2. Execute Natural Language Query

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me top 5 customers by YTD sales",
    "max_rows": 10
  }'
```

**Expected Response:**
```json
{
    "success": true,
    "query": {
        "question": "Show me top 5 customers by YTD sales",
        "sql": "SELECT ...",
        "generated_at": "2025-12-31T11:27:13.777985+00:00",
        "execution_time_ms": 108.85
    },
    "rows": [
        {
            "gws_cust_name": "V J INFONET PVT LTD",
            "gws_ytd_sales": "72898108"
        },
        ...
    ],
    "row_count": 5,
    "execution_time_ms": 150.23
}
```

---

### 3. Save Report

```bash
curl -X POST http://localhost:8000/api/v1/reports \
  -H "Content-Type: application/json" \
  -d '{
    "report_name": "Top 5 Customers by YTD Sales",
    "user_question": "Show me top 5 customers by YTD sales",
    "generated_sql": "SELECT gws_cust_name, gws_ytd_sales FROM public.gwanalytics WHERE gws_ytd_sales IS NOT NULL ORDER BY gws_ytd_sales DESC LIMIT 5;",
    "user_id": "test_user_123",
    "report_description": "Monthly top customers report",
    "tags": ["sales", "customers", "top"],
    "is_favorite": true
  }'
```

**Expected Response:**
```json
{
    "success": true,
    "report": {
        "report_id": 1,
        "report_name": "Top 5 Customers by YTD Sales",
        "user_question": "Show me top 5 customers by YTD sales",
        "generated_sql": "SELECT ...",
        "user_id": "test_user_123",
        "created_at": "2025-12-31T11:27:13.777985+00:00",
        "updated_at": null,
        "last_executed_at": null,
        "execution_count": 0,
        "is_favorite": true,
        "report_description": "Monthly top customers report",
        "tags": ["sales", "customers", "top"],
        "status": "active"
    }
}
```

---

### 4. Get Report by ID

```bash
curl -X GET "http://localhost:8000/api/v1/reports/1?user_id=test_user_123"
```

**Expected Response:**
```json
{
    "success": true,
    "report": {
        "report_id": 1,
        "report_name": "Top 5 Customers by YTD Sales",
        ...
    }
}
```

---

### 5. List User Reports

```bash
curl -X GET "http://localhost:8000/api/v1/reports?user_id=test_user_123&limit=10&offset=0"
```

**Expected Response:**
```json
{
    "success": true,
    "reports": [
        {
            "report_id": 1,
            "report_name": "Top 5 Customers by YTD Sales",
            ...
        }
    ],
    "total": 1,
    "limit": 10,
    "offset": 0
}
```

---

### 6. Update Report

```bash
curl -X PUT "http://localhost:8000/api/v1/reports/1?user_id=test_user_123" \
  -H "Content-Type: application/json" \
  -d '{
    "report_name": "Updated: Top 5 Customers by YTD Sales",
    "report_description": "Updated description"
  }'
```

**Expected Response:**
```json
{
    "success": true,
    "report": {
        "report_id": 1,
        "report_name": "Updated: Top 5 Customers by YTD Sales",
        ...
    }
}
```

---

### 7. Execute Saved Report

```bash
curl -X POST "http://localhost:8000/api/v1/reports/1/execute?user_id=test_user_123" \
  -H "Content-Type: application/json" \
  -d '{
    "max_rows": 10
  }'
```

**Expected Response:**
```json
{
    "success": true,
    "report": {
        "report_id": 1,
        ...
    },
    "rows": [
        {
            "gws_cust_name": "V J INFONET PVT LTD",
            "gws_ytd_sales": "72898108"
        },
        ...
    ],
    "row_count": 5,
    "execution_time_ms": 120.45
}
```

---

### 8. Delete Report

```bash
curl -X DELETE "http://localhost:8000/api/v1/reports/1?user_id=test_user_123"
```

**Expected Response:**
```json
{
    "success": true,
    "message": "Report 1 deleted successfully"
}
```

---

## Error Handling Tests

### Invalid Query (Empty Question)

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "",
    "max_rows": 10
  }'
```

**Expected Response:** `422 Unprocessable Entity`
```json
{
    "error": "Validation error",
    "detail": [
        {
            "type": "string_too_short",
            "loc": ["body", "question"],
            "msg": "String should have at least 1 character"
        }
    ]
}
```

---

### Missing Required Field

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "max_rows": 10
  }'
```

**Expected Response:** `422 Unprocessable Entity`
```json
{
    "error": "Validation error",
    "detail": [
        {
            "type": "missing",
            "loc": ["body", "question"],
            "msg": "Field required"
        }
    ]
}
```

---

### Non-existent Report

```bash
curl -X GET "http://localhost:8000/api/v1/reports/99999?user_id=test_user_123"
```

**Expected Response:** `500 Internal Server Error`
```json
{
    "error": "An error occurred",
    "detail": "An unexpected error occurred. Please try again."
}
```

---

## Automated Testing

Run the comprehensive test suite:

```bash
cd backend
./test_api_with_curl.sh
```

This script will:
- Test all endpoints
- Verify responses
- Handle JSON encoding properly
- Show colored output
- Provide a summary

---

## Notes

1. **SQL Escaping**: When saving reports, the SQL query must be properly JSON-escaped. The test script handles this automatically using Python's `json.dumps()`.

2. **User ID**: All report operations require a `user_id` parameter to ensure users can only access their own reports.

3. **Status Codes**:
   - `200 OK` - Success
   - `201 Created` - Resource created successfully
   - `422 Unprocessable Entity` - Validation error
   - `500 Internal Server Error` - Server error (generic for security)

4. **Response Format**: All successful responses include a `success: true` field.

5. **Error Format**: All errors follow a consistent format with `error` and `detail` fields.

---

## Server Logs

To view server logs:
```bash
tail -f /tmp/api_server.log
```

Or if running in foreground:
```bash
uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

---

**Last Updated**: December 31, 2024  
**Test Status**: ✅ All 11 tests passing

