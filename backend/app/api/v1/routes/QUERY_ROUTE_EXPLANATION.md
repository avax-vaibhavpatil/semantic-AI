# Query Route - Code Flow Explanation

This document explains the first API route we created: **POST /api/v1/query**

---

## What This Route Does

**Endpoint:** `POST /api/v1/query`

**Purpose:** Execute natural language queries and return SQL results

**Example Request:**
```json
POST /api/v1/query
{
  "question": "Show me top 5 customers by sales",
  "max_rows": 100
}
```

**Example Response:**
```json
{
  "success": true,
  "query": {
    "question": "Show me top 5 customers by sales",
    "sql": "SELECT ...",
    "generated_at": "2025-12-30T10:00:00Z"
  },
  "rows": [{"customer": "ABC", "sales": 1000}],
  "row_count": 1,
  "execution_time_ms": 123.45,
  "warning": null
}
```

---

## Code Structure

The route is in: `backend/app/api/v1/routes/query.py`

### 1. Request/Response Models (Pydantic)

**Why Pydantic?**
- Automatic validation (checks data types, min/max values)
- Automatic documentation (Swagger UI)
- Type safety

**QueryRequestModel:**
```python
class QueryRequestModel(BaseModel):
    question: str  # Required, min 1 character
    max_rows: int = 500  # Optional, default 500, between 1-10000
    dialect: Optional[str] = None  # Optional SQL dialect
```

**QueryResponseModel:**
```python
class QueryResponseModel(BaseModel):
    success: bool
    query: dict  # Query metadata
    rows: list  # Results
    row_count: int
    execution_time_ms: float
    warning: Optional[str] = None
```

---

### 2. Dependency Injection

**Function:** `get_query_service()`

**What it does:**
- Creates `QueryService` with all dependencies
- Called by FastAPI for each request
- Returns `QueryService` instance

**Flow:**
```
FastAPI Request
    ↓ calls
get_query_service()
    ↓ creates
FileSemanticRepository
    ↓ creates
ClaudeProvider, GroqProvider
    ↓ creates
ProviderRouter (with providers)
    ↓ creates
QueryService (with repo + router)
    ↓ returns
QueryService instance
```

**Why dependency injection?**
- FastAPI handles lifecycle (creates per request)
- Easy to test (can override in tests)
- Clean separation of concerns

---

### 3. Route Handler

**Function:** `execute_query()`

**Decorator:** `@router.post("", response_model=QueryResponseModel)`

**Parameters:**
- `request: QueryRequestModel` - From request body (validated by Pydantic)
- `query_service: QueryService = Depends(get_query_service)` - Injected by FastAPI

**Flow:**
```
1. Frontend sends POST /api/v1/query
   ↓
2. FastAPI validates request (Pydantic)
   ↓
3. FastAPI calls get_query_service() → returns QueryService
   ↓
4. execute_query() function runs:
   a. Convert QueryRequestModel → QueryRequest (domain model)
   b. Call query_service.execute_query(query_request)
   c. Get QueryResult (domain model)
   d. Convert QueryResult → QueryResponseModel (Pydantic)
   e. Return JSON response
```

---

## Step-by-Step Code Flow

### Step 1: Request Validation
```python
request: QueryRequestModel  # Pydantic validates automatically
```
- Checks `question` is not empty
- Checks `max_rows` is between 1-10000
- Returns 422 if validation fails

### Step 2: Convert to Domain Model
```python
query_request = QueryRequest(
    question=request.question,
    max_rows=request.max_rows,
    dialect=request.dialect,
)
```
- Converts Pydantic model → Domain model
- Domain model is framework-independent

### Step 3: Execute Query
```python
query_result: QueryResult = await query_service.execute_query(query_request)
```
- Calls service layer
- Service handles: semantic layer → AI → SQL → Database
- Returns `QueryResult` domain model

### Step 4: Error Handling
```python
except QueryValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
except SQLGenerationError as e:
    raise HTTPException(status_code=500, detail=f"Failed to generate SQL: {e}")
```
- Converts domain exceptions → HTTP exceptions
- Returns appropriate status codes

### Step 5: Convert to Response Model
```python
response = QueryResponseModel(
    success=True,
    query={...},
    rows=query_result.rows,
    ...
)
```
- Converts domain model → Pydantic model
- Prepares JSON response

### Step 6: Return Response
```python
return response  # FastAPI converts to JSON automatically
```

---

## Error Handling

| Domain Exception | HTTP Status | When It Happens |
|-----------------|-------------|-----------------|
| `QueryValidationError` | 400 Bad Request | Invalid question or parameters |
| `SQLGenerationError` | 500 Internal Server Error | AI fails to generate SQL |
| `SQLExecutionError` | 500 Internal Server Error | Database query fails |
| `Exception` (unexpected) | 500 Internal Server Error | Any other error |

---

## Key Concepts

### 1. **Pydantic Models** (Request/Response)
- **Purpose:** Validate and serialize data
- **Used for:** API contracts (what frontend sends/receives)
- **Location:** API layer only

### 2. **Domain Models** (QueryRequest, QueryResult)
- **Purpose:** Business logic representation
- **Used for:** Service layer communication
- **Location:** Core layer (framework-independent)

### 3. **Dependency Injection**
- **Purpose:** Provide services to routes
- **How:** FastAPI's `Depends()` function
- **Benefit:** Easy to test, clean code

### 4. **Error Conversion**
- **Domain exceptions** → **HTTP exceptions**
- Keeps business logic separate from HTTP concerns

---

## File Structure

```
backend/app/api/
├── main.py                    # FastAPI app setup
└── v1/
    ├── __init__.py            # Router aggregation
    └── routes/
        ├── __init__.py
        └── query.py           # Query route (this file)
```

---

## How to Test

### Using curl:
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me top 5 customers by sales",
    "max_rows": 100
  }'
```

### Using Swagger UI:
1. Start server: `uvicorn app.api.main:app --reload`
2. Open: `http://localhost:8000/docs`
3. Find `/api/v1/query` endpoint
4. Click "Try it out"
5. Enter request body
6. Click "Execute"

---

## Next Steps

Now you can create the next route! Here's what to do:

1. **Create new route file:** `backend/app/api/v1/routes/report.py`
2. **Follow the same pattern:**
   - Request/Response models (Pydantic)
   - Dependency injection function
   - Route handler function
   - Error handling

3. **Register route:** Add to `backend/app/api/v1/__init__.py`

**Example structure for report route:**
```python
# Similar to query.py but for reports
router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("", response_model=SaveReportResponseModel)
async def save_report(...):
    # Similar pattern to query route
    pass
```

---

## Summary

✅ **Created:** First route (POST /api/v1/query)
✅ **Pattern:** Request → Service → Response
✅ **Error Handling:** Domain exceptions → HTTP exceptions
✅ **Dependency Injection:** Clean service initialization
✅ **Documentation:** Auto-generated Swagger docs

**Ready for you to create the next route!** 🚀

