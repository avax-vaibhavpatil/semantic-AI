# System Design: Multi-User Handling & Load Balancing

## Table of Contents
1. [How We Handle Multiple Users](#how-we-handle-multiple-users)
2. [Load Balancing Concepts](#load-balancing-concepts)
3. [Code-Level Understanding](#code-level-understanding)
4. [Architecture Flow](#architecture-flow)
5. [Scalability Considerations](#scalability-considerations)
6. [Current vs. Production Architecture](#current-vs-production-architecture)

---

## How We Handle Multiple Users

### 🎯 Current Architecture: Single Server with Async/Await

**Key Concept:** FastAPI uses **async/await** and an **event loop** to handle multiple requests concurrently on a single server.

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Server (Single Process)           │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Event Loop (asyncio)                        │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │ Request  │  │ Request  │  │ Request  │  ...     │   │
│  │  │   #1     │  │   #2     │  │   #3     │          │   │
│  │  │ (async)  │  │ (async)  │  │ (async)  │          │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘          │   │
│  │       │             │             │                  │   │
│  │       └─────────────┴─────────────┘                  │   │
│  │                    │                                  │   │
│  │              [Event Loop]                            │   │
│  │         (Manages all async tasks)                    │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │                                       │
│  ┌────────────────────▼─────────────────────────────────┐   │
│  │         Shared Services (Singleton)                   │   │
│  │  • QueryService (ONE instance, reused)                │   │
│  │  • SemanticRepository (ONE instance, reused)          │   │
│  │  • AI Router (ONE instance, reused)                  │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │      Database Connection Pool (20 connections)       │   │
│  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ... (up to 20)         │   │
│  │  │Conn│ │Conn│ │Conn│ │Conn│                         │   │
│  │  └────┘ └────┘ └────┘ └────┘                         │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Key Mechanisms

#### 1. **Event Loop (asyncio)**
- **What:** Python's event loop manages all async tasks
- **How:** When a request comes in, it's added to the event loop
- **Benefit:** While waiting for DB/AI, the server can handle other requests

#### 2. **Async/Await Pattern**
- **What:** Non-blocking I/O operations
- **How:** When code hits `await`, it yields control back to the event loop
- **Benefit:** Server doesn't block waiting for slow operations

#### 3. **Connection Pooling**
- **What:** Pre-created database connections ready to use
- **How:** Pool of 20 connections shared across all requests
- **Benefit:** No need to create new connections per request

#### 4. **Singleton Services**
- **What:** Services created once at startup, reused for all requests
- **How:** Services initialized in `startup_event()`, stored in global variable
- **Benefit:** No overhead of creating services per request

---

## Load Balancing Concepts

### 🎯 What is Load Balancing?

**Load balancing** distributes incoming requests across multiple servers to:
- **Handle more users** (horizontal scaling)
- **Improve reliability** (if one server fails, others continue)
- **Reduce latency** (requests go to less busy servers)

### Current State: No Load Balancer (Single Server)

```
┌─────────┐
│ Client  │
└────┬────┘
     │
     │ HTTP Request
     │
┌────▼────────────────────┐
│   FastAPI Server        │
│   (Single Instance)     │
│   Port: 8000            │
└─────────────────────────┘
```

**Limitations:**
- ❌ Single point of failure
- ❌ Limited by one server's CPU/RAM
- ❌ Can't handle unlimited users

### Production Architecture: With Load Balancer

```
┌─────────┐
│ Client  │
└────┬────┘
     │
     │ HTTP Request
     │
┌────▼────────────────────┐
│   Load Balancer         │
│   (Nginx / HAProxy /    │
│    AWS ALB / etc.)      │
└────┬────────────────────┘
     │
     ├──────────┬──────────┬──────────┐
     │          │          │          │
┌────▼───┐ ┌───▼───┐ ┌───▼───┐ ┌───▼───┐
│Server 1│ │Server │ │Server │ │Server │
│:8000   │ │2:8000 │ │3:8000 │ │N:8000 │
└────────┘ └───────┘ └───────┘ └───────┘
```

**Benefits:**
- ✅ Handles more users (distributed across servers)
- ✅ High availability (if one server fails, others continue)
- ✅ Better performance (requests go to less busy servers)

### Load Balancing Strategies

#### 1. **Round Robin** (Default)
```
Request 1 → Server 1
Request 2 → Server 2
Request 3 → Server 3
Request 4 → Server 1 (cycle repeats)
```

#### 2. **Least Connections**
```
Request → Server with fewest active connections
```

#### 3. **IP Hash**
```
Request from IP 1.2.3.4 → Always goes to Server 1
Request from IP 5.6.7.8 → Always goes to Server 2
```

#### 4. **Weighted Round Robin**
```
Server 1 (weight: 3) → Gets 3 requests
Server 2 (weight: 1) → Gets 1 request
```

---

## Code-Level Understanding

### 1. FastAPI App Initialization (`app/api/main.py`)

```python
# Line 34-38: Create FastAPI app
app = FastAPI(
    title="Auto Semantic BI Platform API",
    description="AI-powered natural language to SQL query platform",
    version="1.0.0",
)
```

**What happens:**
- FastAPI creates an **event loop** (asyncio)
- Sets up **async request handling**
- Each request runs in an **async context**

### 2. Service Initialization (Singleton Pattern)

```python
# Line 77-89: Startup event
@app.on_event("startup")
async def startup_event():
    """
    Called when the application starts.
    
    CRITICAL: Initialize all services here (once, not per request).
    This prevents creating heavy objects (repositories, AI providers) on every request.
    """
    logger.info("🚀 Auto Semantic BI Platform API starting...")
    
    # Initialize services at startup (singleton pattern)
    initialize_services()
```

**What happens:**
- Services created **ONCE** at startup
- Stored in **global variable** (`_query_service`)
- **Reused** for all requests

**Code Flow:**
```
App Startup
    ↓
startup_event() called
    ↓
initialize_services() called
    ↓
QueryService created (ONCE)
    ↓
Stored in _query_service (global)
    ↓
All requests use same instance
```

### 3. Dependency Injection (`app/api/dependencies.py`)

```python
# Line 62-74: Get service (singleton)
def get_query_service() -> QueryService:
    """
    Get QueryService instance (singleton).
    
    CRITICAL: Returns pre-initialized service, does NOT create new instances.
    This ensures QueryService is created ONCE and reused.
    """
    if _query_service is None:
        raise RuntimeError("Services not initialized. Call initialize_services() at app startup.")
    return _query_service
```

**What happens:**
- FastAPI calls `get_query_service()` for each request
- Returns **same instance** (not creating new one)
- All requests **share** the same QueryService

**Request Flow:**
```
Request 1 arrives
    ↓
FastAPI calls get_query_service()
    ↓
Returns _query_service (same instance)
    ↓
Request 1 uses QueryService

Request 2 arrives (at same time)
    ↓
FastAPI calls get_query_service()
    ↓
Returns _query_service (SAME instance)
    ↓
Request 2 uses QueryService (concurrently)
```

### 4. Async Route Handler (`app/api/v1/routes/query.py`)

```python
# Line 108-187: Query endpoint
@router.post("", response_model=QueryResponseModel)
async def execute_query(
    request: QueryRequestModel,
    query_service: QueryService = Depends(get_query_service),
):
    """
    Execute a natural language query.
    """
    # Step 1: Convert to domain model
    query_request = QueryRequest(...)
    
    # Step 2: Execute query (ASYNC - doesn't block)
    query_result: QueryResult = await query_service.execute_query(query_request)
    
    # Step 3: Return response
    return response
```

**What happens:**
- `async def` makes this function **non-blocking**
- When `await` is called, control yields to event loop
- Other requests can be processed while waiting

**Concurrent Request Flow:**
```
Time 0ms:  Request 1 arrives → starts processing
Time 10ms: Request 2 arrives → starts processing (Request 1 still running)
Time 20ms: Request 3 arrives → starts processing (Request 1 & 2 still running)

Time 50ms: Request 1 hits "await query_service.execute_query()"
           → Yields to event loop
           → Request 2 continues processing

Time 60ms: Request 2 hits "await query_service.execute_query()"
           → Yields to event loop
           → Request 3 continues processing

Time 100ms: Request 1's DB query completes
            → Continues processing
            → Returns response

Time 150ms: Request 2's DB query completes
            → Continues processing
            → Returns response
```

### 5. Database Connection Pool (`app/infrastructure/database/connection.py`)

```python
# Line 86-96: Create async engine with connection pool
_async_engine = create_async_engine(
    async_url,
    pool_pre_ping=True,      # Check connection before using
    pool_size=20,            # Keep 20 connections ready
    max_overflow=40,         # Can create 40 more if needed
    pool_recycle=3600,       # Recycle connections after 1 hour
    echo=settings.debug,
    future=True
)
```

**What happens:**
- **20 connections** pre-created and ready
- When request needs DB, it **borrows** a connection from pool
- After query completes, connection **returned** to pool
- If all 20 busy, can create up to **40 more** (total 60)

**Connection Pool Flow:**
```
Request 1 needs DB
    ↓
Borrows connection from pool (20 available)
    ↓
Executes query
    ↓
Returns connection to pool
    ↓
Connection available for next request

Request 2 needs DB (while Request 1 using connection)
    ↓
Borrows DIFFERENT connection from pool (19 available)
    ↓
Executes query concurrently
    ↓
Returns connection to pool
```

### 6. Async Query Execution (`app/infrastructure/database/query_executor.py`)

```python
# Line 15-57: Execute query asynchronously
async def execute_query(
    sql: str,
    engine: Optional[AsyncEngine] = None,
    max_rows: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Execute a raw SQL SELECT query asynchronously
    """
    # Execute query asynchronously
    rows: List[Dict[str, Any]] = []
    async with engine.connect() as conn:
        result = await conn.stream(text(safe_sql))
        # Convert rows to dictionaries
        async for row in result:
            rows.append(dict(row._mapping))
    return rows
```

**What happens:**
- `async with engine.connect()` **borrows** connection from pool
- `await conn.stream()` **yields** to event loop while waiting for DB
- Other requests can use other connections **concurrently**
- When DB responds, execution continues

**Concurrent Query Flow:**
```
Request 1: await execute_query("SELECT ...")
    ↓
Borrows connection 1 from pool
    ↓
Sends SQL to PostgreSQL
    ↓
Yields to event loop (waiting for DB response)

Request 2: await execute_query("SELECT ...")
    ↓
Borrows connection 2 from pool (different connection!)
    ↓
Sends SQL to PostgreSQL
    ↓
Yields to event loop (waiting for DB response)

PostgreSQL responds to Request 1
    ↓
Request 1 continues, returns results

PostgreSQL responds to Request 2
    ↓
Request 2 continues, returns results
```

---

## Architecture Flow

### Complete Request Flow (Single User)

```
┌─────────┐
│ Client  │
└────┬────┘
     │
     │ POST /api/v1/query
     │ {"question": "Show top 5 customers"}
     │
┌────▼─────────────────────────────────────────────┐
│  FastAPI Server                                  │
│                                                  │
│  1. Route Handler (query.py)                    │
│     async def execute_query(...)                │
│         ↓                                        │
│  2. Dependency Injection                         │
│     get_query_service()                          │
│     → Returns singleton QueryService            │
│         ↓                                        │
│  3. QueryService.execute_query()                │
│     a. Load semantic layer (async)               │
│     b. Build AI prompt                          │
│     c. Call AI router (async)                   │
│        → ClaudeProvider.generate_sql()          │
│        → HTTP request to Anthropic API           │
│        → Yields to event loop (waiting)          │
│     d. Receive SQL from AI                      │
│     e. Execute SQL (async)                       │
│        → execute_query()                        │
│        → Borrow connection from pool             │
│        → Send SQL to PostgreSQL                  │
│        → Yields to event loop (waiting)          │
│     f. Receive results from DB                   │
│     g. Format results                            │
│         ↓                                        │
│  4. Return QueryResult                           │
│         ↓                                        │
│  5. Convert to QueryResponseModel                │
│         ↓                                        │
│  6. Return JSON to client                        │
└──────────────────────────────────────────────────┘
```

### Concurrent Request Flow (Multiple Users)

```
Time 0ms:
┌─────────────────────────────────────────────────────┐
│  Event Loop                                         │
│                                                     │
│  Request 1: "Show top 5 customers"                │
│    → Started processing                            │
│    → Loading semantic layer...                     │
│                                                     │
│  Request 2: "Show total sales"                     │
│    → Started processing (concurrently)              │
│    → Loading semantic layer...                     │
│                                                     │
│  Request 3: "Show customers by profit"             │
│    → Started processing (concurrently)             │
│    → Loading semantic layer...                     │
└─────────────────────────────────────────────────────┘

Time 50ms:
┌─────────────────────────────────────────────────────┐
│  Event Loop                                         │
│                                                     │
│  Request 1: await AI call (yielded to event loop) │
│    → Waiting for Claude API response               │
│                                                     │
│  Request 2: await AI call (yielded to event loop)  │
│    → Waiting for Claude API response               │
│                                                     │
│  Request 3: await AI call (yielded to event loop)  │
│    → Waiting for Claude API response               │
│                                                     │
│  [Event loop can handle more requests here]        │
└─────────────────────────────────────────────────────┘

Time 200ms:
┌─────────────────────────────────────────────────────┐
│  Event Loop                                         │
│                                                     │
│  Request 1: AI responded, now executing SQL        │
│    → Borrowed connection 1 from pool               │
│    → await DB query (yielded to event loop)       │
│                                                     │
│  Request 2: AI responded, now executing SQL        │
│    → Borrowed connection 2 from pool               │
│    → await DB query (yielded to event loop)        │
│                                                     │
│  Request 3: AI responded, now executing SQL        │
│    → Borrowed connection 3 from pool                │
│    → await DB query (yielded to event loop)        │
└─────────────────────────────────────────────────────┘

Time 300ms:
┌─────────────────────────────────────────────────────┐
│  Event Loop                                         │
│                                                     │
│  Request 1: DB responded, returning results        │
│    → Returns connection 1 to pool                  │
│    → Response sent to client                       │
│                                                     │
│  Request 2: DB responded, returning results        │
│    → Returns connection 2 to pool                   │
│    → Response sent to client                       │
│                                                     │
│  Request 3: DB responded, returning results       │
│    → Returns connection 3 to pool                  │
│    → Response sent to client                       │
└─────────────────────────────────────────────────────┘
```

---

## Scalability Considerations

### Current Limitations

#### 1. **Single Server**
- **Limit:** One server = one CPU/RAM limit
- **Solution:** Add load balancer + multiple servers

#### 2. **Connection Pool Size**
- **Current:** 20 connections (max 60 with overflow)
- **Limit:** If 60+ concurrent DB queries, new requests wait
- **Solution:** Increase pool size or add read replicas

#### 3. **AI API Rate Limits**
- **Current:** Claude/Groq have rate limits
- **Limit:** Too many requests = 429 errors
- **Solution:** Add request queuing or caching

#### 4. **Memory Usage**
- **Current:** All query results loaded into memory
- **Limit:** Large results = high memory usage
- **Solution:** Use streaming for large results

### Scaling Strategies

#### 1. **Horizontal Scaling (Add More Servers)**

```
Before:
Client → FastAPI Server (1 instance)

After:
Client → Load Balancer → FastAPI Server 1
                        → FastAPI Server 2
                        → FastAPI Server 3
```

**Implementation:**
- Use **Nginx** or **HAProxy** as load balancer
- Deploy multiple FastAPI instances
- Configure load balancer to distribute requests

#### 2. **Database Read Replicas**

```
Before:
FastAPI → PostgreSQL (single instance)

After:
FastAPI → PostgreSQL Primary (writes)
       → PostgreSQL Replica 1 (reads)
       → PostgreSQL Replica 2 (reads)
```

**Implementation:**
- Set up PostgreSQL replication
- Route read queries to replicas
- Route write queries to primary

#### 3. **Caching Layer**

```
Before:
Request → QueryService → AI → Database

After:
Request → Cache (Redis) → If hit, return cached result
       → If miss, QueryService → AI → Database → Cache result
```

**Implementation:**
- Add **Redis** for caching
- Cache common queries
- Set TTL (time-to-live) for cache entries

#### 4. **Request Queuing**

```
Before:
Request → AI API (if rate limited, fails)

After:
Request → Queue (RabbitMQ/Kafka) → Worker → AI API
```

**Implementation:**
- Add message queue (RabbitMQ, Kafka)
- Workers process queue
- Handles rate limits gracefully

---

## Current vs. Production Architecture

### Current Architecture (Development)

```
┌─────────┐
│ Client  │
└────┬────┘
     │
┌────▼────────────────────┐
│   FastAPI Server        │
│   (Single Instance)     │
│   - Async/Await         │
│   - Singleton Services  │
│   - Connection Pool     │
└────┬────────────────────┘
     │
┌────▼────────────────────┐
│   PostgreSQL            │
│   (Single Instance)     │
└─────────────────────────┘
```

**Characteristics:**
- ✅ Handles multiple users concurrently (async)
- ✅ Efficient resource usage (singleton, pooling)
- ❌ Single point of failure
- ❌ Limited by one server's capacity

### Production Architecture (Recommended)

```
┌─────────┐
│ Client  │
└────┬────┘
     │
┌────▼────────────────────┐
│   Load Balancer         │
│   (Nginx/HAProxy/ALB)   │
│   - Health checks        │
│   - SSL termination     │
│   - Rate limiting       │
└────┬────────────────────┘
     │
     ├──────────┬──────────┬──────────┐
     │          │          │          │
┌────▼───┐ ┌───▼───┐ ┌───▼───┐ ┌───▼───┐
│FastAPI │ │FastAPI│ │FastAPI│ │FastAPI│
│Server 1│ │Server │ │Server │ │Server │
│        │ │2      │ │3      │ │N      │
└────┬───┘ └───┬───┘ └───┬───┘ └───┬───┘
     │          │          │          │
     └──────────┴──────────┴──────────┘
                    │
     ┌──────────────┴──────────────┐
     │                             │
┌────▼──────────┐         ┌───────▼────────┐
│  PostgreSQL   │         │  Redis Cache   │
│  Primary      │         │  (Optional)     │
│  + Replicas   │         └────────────────┘
└───────────────┘
```

**Characteristics:**
- ✅ High availability (multiple servers)
- ✅ Horizontal scaling (add more servers as needed)
- ✅ Load distribution (requests spread across servers)
- ✅ Fault tolerance (if one server fails, others continue)

---

## Summary

### How We Handle Multiple Users (Current)

1. **Async/Await:** FastAPI uses event loop to handle concurrent requests
2. **Singleton Services:** Services created once, reused for all requests
3. **Connection Pooling:** Database connections shared efficiently
4. **Non-blocking I/O:** While waiting for DB/AI, server handles other requests

### Load Balancing (Future)

1. **Current:** Single server (no load balancer)
2. **Production:** Add load balancer + multiple servers
3. **Benefits:** More users, high availability, better performance

### Key Takeaways

- ✅ **Current system handles multiple users** via async/await
- ✅ **Efficient resource usage** via singleton + pooling
- ⚠️ **Single server limitation** (add load balancer for production)
- 🚀 **Ready to scale** (architecture supports horizontal scaling)

---

## Code References

- **App Initialization:** `backend/app/api/main.py` (lines 34-97)
- **Service Singleton:** `backend/app/api/dependencies.py` (lines 20-84)
- **Async Route:** `backend/app/api/v1/routes/query.py` (lines 108-187)
- **DB Connection Pool:** `backend/app/infrastructure/database/connection.py` (lines 86-96)
- **Async Query Execution:** `backend/app/infrastructure/database/query_executor.py` (lines 15-57)

