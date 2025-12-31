# Code Walkthrough: How Concurrent Requests Work

## Real Example: 3 Users Querying Simultaneously

Let's trace through **exactly** what happens in the code when 3 users make queries at the same time.

---

## Scenario

**Time 0ms:** 3 users send requests simultaneously:
- **User 1:** "Show me top 5 customers"
- **User 2:** "Show me total sales"
- **User 3:** "Show me customers by profit"

---

## Step-by-Step Code Execution

### Step 1: Requests Arrive at FastAPI (`app/api/main.py`)

```python
# Line 34-38: FastAPI app created at startup
app = FastAPI(
    title="Auto Semantic BI Platform API",
    version="1.0.0",
)
```

**What happens:**
- FastAPI creates an **event loop** (asyncio)
- Event loop is **ready** to handle async requests

**At Time 0ms:**
```
Event Loop State:
┌─────────────────────────────────────┐
│  Request 1: Queued                  │
│  Request 2: Queued                  │
│  Request 3: Queued                  │
└─────────────────────────────────────┘
```

---

### Step 2: FastAPI Routes Requests (`app/api/v1/routes/query.py`)

```python
# Line 108-112: Route handler
@router.post("", response_model=QueryResponseModel)
async def execute_query(
    request: QueryRequestModel,
    query_service: QueryService = Depends(get_query_service),
):
```

**What happens:**
- FastAPI sees 3 requests for `/api/v1/query`
- Creates **3 separate async tasks** (one per request)
- All 3 tasks start executing **concurrently**

**At Time 1ms:**
```
Event Loop State:
┌─────────────────────────────────────┐
│  Task 1 (User 1):                   │
│    → execute_query() started         │
│    → FastAPI calls get_query_service()│
│                                      │
│  Task 2 (User 2):                   │
│    → execute_query() started         │
│    → FastAPI calls get_query_service()│
│                                      │
│  Task 3 (User 3):                   │
│    → execute_query() started         │
│    → FastAPI calls get_query_service()│
└─────────────────────────────────────┘
```

---

### Step 3: Dependency Injection (`app/api/dependencies.py`)

```python
# Line 62-74: Get service (singleton)
def get_query_service() -> QueryService:
    """
    Get QueryService instance (singleton).
    """
    if _query_service is None:
        raise RuntimeError("Services not initialized...")
    return _query_service  # Returns SAME instance for all requests
```

**What happens:**
- **All 3 requests** call `get_query_service()` at the same time
- **All 3 get the SAME QueryService instance** (singleton)
- No conflicts because QueryService is **stateless** (no shared mutable state per request)

**At Time 2ms:**
```
Memory State:
┌─────────────────────────────────────┐
│  Global Variable:                   │
│  _query_service = QueryService(...) │
│  (Created at startup, ONE instance) │
│                                      │
│  Task 1: query_service = _query_service│
│  Task 2: query_service = _query_service│
│  Task 3: query_service = _query_service│
│  (All pointing to SAME object)      │
└─────────────────────────────────────┘
```

**Why this works:**
- QueryService doesn't store request-specific data
- Each request's data is passed as parameters
- No race conditions because no shared mutable state

---

### Step 4: QueryService Execution (`app/services/query_service.py`)

```python
# Line 62-86: Execute query
async def execute_query(
    self,
    request: QueryRequest,
) -> QueryResult:
    """
    Execute a natural language query.
    """
    start_time = time.time()
    logger.info(f"Executing query: {request.question[:50]}...")
    
    # Step 1: Load semantic layer
    semantic_layer = await self.semantic_repository.load_semantic()
    
    # Step 2: Build AI prompts
    system_prompt = self._build_system_prompt(semantic_layer)
    user_prompt = self._build_user_prompt(request.question)
    
    # Step 3: Generate SQL (ASYNC - yields to event loop)
    sql = await self.ai_router.generate_sql(system_prompt, user_prompt)
    
    # Step 4: Execute SQL (ASYNC - yields to event loop)
    rows = await execute_query(sql, max_rows=request.max_rows)
    
    # Step 5: Return results
    return QueryResult(...)
```

**What happens:**
- **All 3 tasks** call `query_service.execute_query()` concurrently
- Each task has its **own request object** (different question)
- When they hit `await`, they **yield to event loop**

**At Time 10ms:**
```
Event Loop State:
┌─────────────────────────────────────┐
│  Task 1 (User 1):                   │
│    → Loading semantic layer...      │
│    → await semantic_repository...   │
│    → YIELDED to event loop          │
│                                      │
│  Task 2 (User 2):                   │
│    → Loading semantic layer...      │
│    → await semantic_repository...   │
│    → YIELDED to event loop          │
│                                      │
│  Task 3 (User 3):                   │
│    → Loading semantic layer...      │
│    → await semantic_repository...   │
│    → YIELDED to event loop          │
└─────────────────────────────────────┘
```

**Key Point:** All 3 tasks are **waiting** (yielded), but event loop can handle **more requests** if they arrive.

---

### Step 5: Semantic Layer Loading (`app/repositories/semantic_repository.py`)

```python
# FileSemanticRepository.load_semantic()
async def load_semantic(self) -> SemanticLayer:
    """
    Load semantic layer from JSON file.
    """
    # Check cache
    if self._cached_layer is not None:
        return self._cached_layer  # Return cached (fast!)
    
    # Load from file (async file I/O)
    async with aiofiles.open(self.file_path, 'r') as f:
        content = await f.read()
    
    # Parse and cache
    self._cached_layer = SemanticLayer.from_dict(data)
    return self._cached_layer
```

**What happens:**
- **All 3 tasks** call `load_semantic()` at the same time
- First task loads from file, **caches** it
- Other 2 tasks get **cached version** (instant return)
- File I/O is **async** (doesn't block)

**At Time 15ms:**
```
Memory State:
┌─────────────────────────────────────┐
│  FileSemanticRepository:            │
│  _cached_layer = SemanticLayer(...) │
│  (Cached after first load)          │
│                                      │
│  Task 1: Got semantic layer (from file)│
│  Task 2: Got semantic layer (from cache)│
│  Task 3: Got semantic layer (from cache)│
└─────────────────────────────────────┘
```

---

### Step 6: AI SQL Generation (`app/infrastructure/ai/router.py`)

```python
# ProviderRouter.generate_sql()
async def generate_sql(
    self,
    system_prompt: str,
    user_prompt: str,
) -> str:
    """
    Generate SQL using AI provider (with fallback).
    """
    # Try Claude first
    try:
        sql = await self.providers[0].generate_sql(...)  # Claude
        return sql
    except RetryableAIError:
        # Fallback to Groq
        sql = await self.providers[1].generate_sql(...)  # Groq
        return sql
```

**What happens:**
- **All 3 tasks** call `generate_sql()` concurrently
- Each makes **separate HTTP request** to Claude API
- `await` **yields to event loop** while waiting for HTTP response
- Event loop can handle **other tasks** while waiting

**At Time 20ms:**
```
Event Loop State:
┌─────────────────────────────────────┐
│  Task 1:                            │
│    → HTTP request to Claude API     │
│    → await http_client.post(...)    │
│    → YIELDED (waiting for response) │
│                                      │
│  Task 2:                            │
│    → HTTP request to Claude API     │
│    → await http_client.post(...)    │
│    → YIELDED (waiting for response) │
│                                      │
│  Task 3:                            │
│    → HTTP request to Claude API     │
│    → await http_client.post(...)    │
│    → YIELDED (waiting for response) │
└─────────────────────────────────────┘

Network:
┌─────────────────────────────────────┐
│  HTTP Request 1 → Claude API        │
│  HTTP Request 2 → Claude API        │
│  HTTP Request 3 → Claude API        │
│  (All sent concurrently)            │
└─────────────────────────────────────┘
```

**Key Point:** All 3 HTTP requests are **in flight** at the same time. Event loop is **not blocked** - it can handle more requests.

---

### Step 7: Database Query Execution (`app/infrastructure/database/query_executor.py`)

```python
# execute_query()
async def execute_query(
    sql: str,
    engine: Optional[AsyncEngine] = None,
    max_rows: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Execute a raw SQL SELECT query asynchronously
    """
    # Get connection from pool
    async with engine.connect() as conn:
        result = await conn.stream(text(safe_sql))
        async for row in result:
            rows.append(dict(row._mapping))
    return rows
```

**What happens:**
- **All 3 tasks** need database connections
- Each **borrows** a connection from the **pool** (20 available)
- All 3 queries execute **concurrently** on PostgreSQL
- `await` **yields to event loop** while waiting for DB response

**At Time 200ms (after AI responds):**
```
Connection Pool State:
┌─────────────────────────────────────┐
│  Pool: 20 connections available     │
│                                      │
│  Task 1:                            │
│    → Borrowed connection 1          │
│    → Executing SQL on PostgreSQL    │
│    → await conn.stream(...)         │
│    → YIELDED (waiting for DB)       │
│                                      │
│  Task 2:                            │
│    → Borrowed connection 2          │
│    → Executing SQL on PostgreSQL    │
│    → await conn.stream(...)         │
│    → YIELDED (waiting for DB)       │
│                                      │
│  Task 3:                            │
│    → Borrowed connection 3          │
│    → Executing SQL on PostgreSQL    │
│    → await conn.stream(...)         │
│    → YIELDED (waiting for DB)       │
└─────────────────────────────────────┘

PostgreSQL:
┌─────────────────────────────────────┐
│  Query 1: Running (connection 1)    │
│  Query 2: Running (connection 2)    │
│  Query 3: Running (connection 3)    │
│  (All executing concurrently)       │
└─────────────────────────────────────┘
```

**Key Point:** PostgreSQL can handle **multiple queries concurrently**. Each connection is **independent**.

---

### Step 8: Results Returned

**At Time 300ms:**
```
Event Loop State:
┌─────────────────────────────────────┐
│  Task 1:                            │
│    → DB responded                   │
│    → Returns connection 1 to pool   │
│    → Formats results                │
│    → Returns response to User 1     │
│    → COMPLETED                      │
│                                      │
│  Task 2:                            │
│    → DB responded                   │
│    → Returns connection 2 to pool   │
│    → Formats results                │
│    → Returns response to User 2     │
│    → COMPLETED                      │
│                                      │
│  Task 3:                            │
│    → DB responded                   │
│    → Returns connection 3 to pool   │
│    → Formats results                │
│    → Returns response to User 3     │
│    → COMPLETED                      │
└─────────────────────────────────────┘
```

---

## Complete Timeline

```
Time    Event
─────────────────────────────────────────────────────────────
0ms     Request 1, 2, 3 arrive at FastAPI
1ms     All 3 tasks start (async def execute_query)
2ms     All 3 get same QueryService (singleton)
10ms    All 3 loading semantic layer (async)
15ms    All 3 got semantic layer (Task 1 from file, 2&3 from cache)
20ms    All 3 making HTTP requests to Claude API (async)
        → All 3 YIELDED to event loop (waiting for HTTP)
        
        [Event loop can handle more requests here]
        
200ms   All 3 got SQL from AI
        All 3 borrowing DB connections from pool
        All 3 executing SQL on PostgreSQL (async)
        → All 3 YIELDED to event loop (waiting for DB)
        
        [Event loop can handle more requests here]
        
300ms   All 3 got results from DB
        All 3 returning connections to pool
        All 3 formatting results
        All 3 returning responses to users
        All 3 COMPLETED
```

---

## Key Code Patterns

### 1. **Async/Await Pattern**

```python
# This is NON-BLOCKING
async def execute_query(...):
    result = await some_async_operation()  # Yields to event loop
    return result
```

**Why:** When `await` is called, control yields to event loop, allowing other tasks to run.

### 2. **Singleton Pattern**

```python
# Created ONCE at startup
_query_service = QueryService(...)

# Reused for ALL requests
def get_query_service():
    return _query_service  # Same instance
```

**Why:** Prevents creating heavy objects (repositories, AI providers) on every request.

### 3. **Connection Pooling**

```python
# Pool created at startup (20 connections)
_async_engine = create_async_engine(..., pool_size=20)

# Each request borrows from pool
async with engine.connect() as conn:  # Borrows connection
    result = await conn.execute(...)
    # Connection returned to pool automatically
```

**Why:** Reusing connections is faster than creating new ones.

### 4. **Stateless Services**

```python
class QueryService:
    def __init__(self, ...):
        self.semantic_repository = ...  # Shared (safe)
        self.ai_router = ...            # Shared (safe)
    
    async def execute_query(self, request: QueryRequest):
        # request is passed as parameter (not stored)
        # No shared mutable state per request
        # Safe for concurrent use
```

**Why:** No shared mutable state = no race conditions.

---

## Why This Works

### ✅ **Event Loop**
- Manages all async tasks
- When task waits (await), switches to another task
- Allows concurrent execution on single thread

### ✅ **Non-Blocking I/O**
- HTTP requests don't block
- Database queries don't block
- File I/O doesn't block
- Server can handle other requests while waiting

### ✅ **Resource Sharing**
- Services shared (singleton)
- Connections shared (pool)
- Memory efficient
- No duplication

### ✅ **Stateless Design**
- No shared mutable state per request
- Each request is independent
- No race conditions

---

## Summary

**How 3 concurrent requests work:**

1. **All 3 start** at the same time (async tasks)
2. **All 3 share** same QueryService (singleton)
3. **All 3 wait** for AI/DB (yield to event loop)
4. **Event loop handles** other requests while waiting
5. **All 3 complete** independently
6. **No conflicts** because services are stateless

**Result:** 3 users get responses in ~300ms each, all handled concurrently! 🚀

