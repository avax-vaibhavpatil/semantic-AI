# Query Service - Code Flow Explanation

This document explains how QueryService works and how code flows through different layers of our architecture.

## What is Query Service?

QueryService is the **CORE business logic** for handling natural language queries.

It orchestrates the complete flow:
1. User asks: "Show me sales by region"
2. Service loads semantic layer (what tables/columns exist)
3. Service asks AI to generate SQL
4. Service executes SQL on database
5. Service returns results

## Code Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER REQUEST                                  │
│  "Show me sales by region"                                       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│              QUERY SERVICE (query_service.py)                   │
│                                                                  │
│  execute_query(QueryRequest)                                    │
│    ↓                                                             │
│  STEP 1: Load Semantic Layer                                   │
│    → semantic_repository.load_semantic()                        │
│    ↓                                                             │
│  STEP 2: Build AI Prompts                                       │
│    → _build_system_prompt()                                     │
│    → _build_user_prompt(question, semantic_layer)              │
│    ↓                                                             │
│  STEP 3: Generate SQL                                           │
│    → ai_router.generate_sql(system_prompt, user_prompt)         │
│    ↓                                                             │
│  STEP 4: Execute SQL                                            │
│    → execute_query(sql, max_rows)                              │
│    ↓                                                             │
│  STEP 5: Return Results                                         │
│    → QueryResult(query, rows, metadata)                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    USER RESPONSE                                 │
│  {                                                               │
│    "rows": [...],                                               │
│    "row_count": 10,                                             │
│    "execution_time_ms": 45.2                                     │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

## Step-by-Step Code Flow

### STEP 1: Service Receives Request

**Location:** `query_service.py`, `execute_query()` method

**Code:**
```python
async def execute_query(self, request: QueryRequest) -> QueryResult:
    # request = QueryRequest(question="Show me sales by region", max_rows=500)
    # This is a domain model from app/core/models/query.py
```

**What happens:**
- Service receives `QueryRequest` (domain model)
- `QueryRequest` contains: question, max_rows, dialect
- Service validates request (already validated by QueryRequest)

**Dependencies used:**
- `QueryRequest` (from `app/core/models/query.py`)
- This is a pure domain model - no database, no API

---

### STEP 2: Load Semantic Layer

**Location:** `query_service.py`, line ~50

**Code:**
```python
semantic_layer = await self.semantic_repository.load_semantic()
```

**Flow:**
```
QueryService
    ↓ calls
SemanticRepository (interface)
    ↓ implemented by
FileSemanticRepository (app/repositories/semantic_repository.py)
    ↓ reads
semantic.json file
    ↓ converts to
SemanticLayer (domain model from app/core/models/semantic.py)
```

**What happens:**
- Service calls repository to load semantic layer
- Repository reads JSON file from filesystem
- Repository converts JSON to `SemanticLayer` domain model
- Service receives `SemanticLayer` object

**Why this design:**
- Service doesn't know **WHERE** semantic layer comes from (file, database, API)
- Service only knows **HOW** to use it (through repository interface)
- Easy to test: can mock `SemanticRepository`
- Easy to change: swap `FileSemanticRepository` for `DatabaseSemanticRepository`

---

### STEP 3: Build AI Prompts

**Location:** `query_service.py`, `_build_system_prompt()` and `_build_user_prompt()`

**Code:**
```python
system_prompt = self._build_system_prompt()
user_prompt = self._build_user_prompt(request.question, semantic_layer)
```

**What happens:**
- System prompt: Instructions for AI ("You are a SQL generator...")
- User prompt: User's question + semantic layer context
- Semantic layer is converted to JSON string for AI

**Flow:**
```
SemanticLayer (domain model)
    ↓ to_dict()
Dictionary
    ↓ json.dumps()
JSON String
    ↓ included in
User Prompt
    ↓ sent to
AI Provider
```

**Why this design:**
- Prompts are business logic (how we talk to AI)
- Service owns prompt building (not infrastructure layer)
- Semantic layer provides context to AI

---

### STEP 4: Generate SQL Using AI

**Location:** `query_service.py`, line ~70

**Code:**
```python
sql = self.ai_router.generate_sql(
    system_prompt=system_prompt,
    user_prompt=user_prompt,
    temperature=0.0,
    max_tokens=1500,
)
```

**Flow:**
```
QueryService
    ↓ calls
ProviderRouter (app/infrastructure/ai/router.py)
    ↓ tries providers in order
ClaudeProvider → GroqProvider → OpenAIProvider
    ↓ calls
AI API (Claude/Groq/OpenAI)
    ↓ returns
SQL String
```

**What happens:**
- Router tries Claude first (primary)
- If Claude fails (retryable error), tries Groq (fallback)
- If Groq fails, tries OpenAI (last resort)
- Returns generated SQL string

**Why this design:**
- Service doesn't know **WHICH** AI provider is used
- Service doesn't know about fallback logic
- Infrastructure handles all AI complexity
- Easy to test: can mock `ProviderRouter`

---

### STEP 5: Create Query Domain Model

**Location:** `query_service.py`, line ~80

**Code:**
```python
query = Query(
    question=request.question,
    sql=sql,
    generated_at=datetime.now(timezone.utc),
)
```

**What happens:**
- Creates `Query` domain model
- `Query` represents: question, SQL, timestamp
- This is our business entity (not just data)

**Why this design:**
- Domain model = business concept
- `Query` is more than just SQL string
- Contains metadata (when generated, etc.)

---

### STEP 6: Execute SQL on Database

**Location:** `query_service.py`, line ~90

**Code:**
```python
rows = await execute_query(
    sql=sql,
    max_rows=request.max_rows,
)
```

**Flow:**
```
QueryService
    ↓ calls
execute_query() (app/infrastructure/database/query_executor.py)
    ↓ uses
AsyncEngine (SQLAlchemy)
    ↓ connects to
PostgreSQL Database
    ↓ executes
SQL Query
    ↓ returns
List[Dict[str, Any]] (rows)
```

**What happens:**
- Service calls database executor
- Executor uses async connection pool
- Executes SQL query
- Returns rows as list of dictionaries
- Respects max_rows limit

**Why this design:**
- Service doesn't know **HOW** database works
- Service doesn't know about connection pooling
- Infrastructure handles all database complexity
- Easy to test: can mock `execute_query`

---

### STEP 7: Build Result and Return

**Location:** `query_service.py`, line ~100

**Code:**
```python
result = QueryResult(
    query=query,
    rows=rows,
    row_count=len(rows),
    execution_time_ms=execution_time_ms,
    executed_at=datetime.now(timezone.utc),
)
```

**What happens:**
- Creates `QueryResult` domain model
- Contains: query, rows, metadata (count, timing)
- Returns complete result to caller

**Why this design:**
- `QueryResult` is a business concept
- Contains all information about query execution
- Can be used by API layer, tests, etc.

---

## Dependency Injection Explanation

QueryService receives dependencies in `__init__`:

```python
def __init__(
    self,
    semantic_repository: SemanticRepository,  # ← Injected
    ai_router: ProviderRouter,                 # ← Injected
):
```

### Why inject dependencies?

1. **TESTABILITY:**
   - Can pass mock repositories in tests
   - Don't need real database or AI for unit tests

2. **FLEXIBILITY:**
   - Can swap implementations easily
   - Use `FileSemanticRepository` in dev, `DatabaseSemanticRepository` in prod

3. **CLEAR DEPENDENCIES:**
   - See exactly what service needs
   - No hidden dependencies

### Example usage:

```python
# In production:
semantic_repo = FileSemanticRepository()
ai_router = build_default_router()
query_service = QueryService(semantic_repo, ai_router)

# In tests:
mock_semantic_repo = MockSemanticRepository()
mock_ai_router = MockAIRouter()
query_service = QueryService(mock_semantic_repo, mock_ai_router)
```

---

## Layer Interactions

QueryService interacts with these layers:

1. **CORE LAYER** (`app/core/`)
   - Uses: `QueryRequest`, `Query`, `QueryResult`, `SemanticLayer`
   - Why: Business domain models

2. **REPOSITORIES LAYER** (`app/repositories/`)
   - Uses: `SemanticRepository` (interface)
   - Why: Data access abstraction

3. **INFRASTRUCTURE LAYER** (`app/infrastructure/`)
   - Uses: `ProviderRouter` (AI), `execute_query` (Database)
   - Why: External system integration

4. **CONFIG LAYER** (`app/config/`)
   - Uses: `get_logger()`
   - Why: Logging configuration

**Service does NOT interact with:**
- API Layer (that's above services)
- Database directly (uses infrastructure)
- AI APIs directly (uses infrastructure)

---

## Error Handling

Service handles errors at each step:

1. **Semantic Layer Loading:**
   - If file not found → Exception raised
   - Service logs error and re-raises

2. **AI SQL Generation:**
   - If all providers fail → Exception raised
   - Router handles fallback automatically
   - Service logs which provider was used

3. **SQL Execution:**
   - If SQL invalid → Database exception
   - Service logs error and re-raises
   - Caller (API layer) handles HTTP error response

**Why re-raise?**
- Service focuses on business logic
- Error formatting is API layer's job
- Service logs for debugging

---

## Testing Strategy

### How to test QueryService:

1. **UNIT TESTS:**
   - Mock `SemanticRepository` (return fake `SemanticLayer`)
   - Mock `ProviderRouter` (return fake SQL)
   - Mock `execute_query` (return fake rows)
   - Test service logic only

2. **INTEGRATION TESTS:**
   - Use real `SemanticRepository` (real file)
   - Use real `ProviderRouter` (real AI, or mock)
   - Use real `execute_query` (test database)
   - Test full flow

3. **WHAT TO TEST:**
   - ✅ Service loads semantic layer correctly
   - ✅ Service builds prompts correctly
   - ✅ Service calls AI router correctly
   - ✅ Service executes SQL correctly
   - ✅ Service returns `QueryResult` correctly
   - ✅ Service handles errors correctly

---

## Summary

QueryService is the **HEART** of our application:

1. It orchestrates the complete query flow
2. It uses dependency injection for flexibility
3. It interacts with multiple layers (Core, Repositories, Infrastructure)
4. It contains business logic (prompt building, result formatting)
5. It's easy to test (can mock all dependencies)

**Next:** We'll build `ReportService` and `SemanticService` following the same patterns!


