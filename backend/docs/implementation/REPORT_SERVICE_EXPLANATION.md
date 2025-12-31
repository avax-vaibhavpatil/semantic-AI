# Report Service - Code Flow Explanation

This document explains how ReportService works and how it manages saved reports.

## What is Report Service?

ReportService manages **saved reports** - queries that users can save and execute later.

**Key Operations:**
1. Save reports (from query results or manually)
2. Retrieve reports by ID
3. List user's reports (with pagination)
4. Search reports (by name, question, description)
5. Update reports
6. Delete reports (soft delete)
7. Execute saved SQL queries

## Code Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER REQUEST                                  │
│  "Save this query as 'Sales Report'"                            │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│              REPORT SERVICE (report_service.py)                 │
│                                                                  │
│  save_report_from_query(QueryResult, name, user_id)             │
│    ↓                                                             │
│  STEP 1: Create Report Domain Model                             │
│    → Extract question, SQL from QueryResult                     │
│    → Create Report(..., report_name, ...)                       │
│    ↓                                                             │
│  STEP 2: Save to Repository                                     │
│    → report_repository.save_report(report)                      │
│    ↓                                                             │
│  STEP 3: Return Report ID                                       │
│    → report_id (int)                                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    USER RESPONSE                                 │
│  { "report_id": 123 }                                           │
└─────────────────────────────────────────────────────────────────┘
```

## Step-by-Step Code Flow

### STEP 1: Save Report from Query Result

**Location:** `report_service.py`, `save_report_from_query()` method

**Code:**
```python
async def save_report_from_query(
    self,
    query_result: QueryResult,
    report_name: str,
    user_id: str,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> int:
```

**Flow:**
```
QueryResult (from QueryService)
    ↓ extract
question, sql
    ↓ create
Report (domain model)
    ↓ save
ReportRepository.save_report()
    ↓ saves to
Database
    ↓ returns
report_id (int)
```

**What happens:**
- Receives `QueryResult` from QueryService
- Extracts question and SQL
- Creates `Report` domain model
- Saves through repository
- Returns report ID

**Why this design:**
- Convenience method - common use case
- Encapsulates conversion logic
- Service owns business logic (how to create report from query)

---

### STEP 2: Get Report by ID

**Location:** `report_service.py`, `get_report()` method

**Code:**
```python
async def get_report(
    self,
    report_id: int,
    user_id: str,
) -> Report:
```

**Flow:**
```
ReportService
    ↓ calls
ReportRepository.get_report(report_id, user_id)
    ↓ queries
Database
    ↓ returns
Report (domain model) or None
    ↓ checks
If None → Raise ReportNotFoundError
If found → Return Report
```

**What happens:**
- Calls repository to get report
- Repository queries database
- If not found, raises `ReportNotFoundError`
- If found, returns `Report` domain model

**Why this design:**
- Service handles business logic (error handling)
- Repository handles data access
- Clear separation of concerns

---

### STEP 3: List Reports

**Location:** `report_service.py`, `list_reports()` method

**Code:**
```python
async def list_reports(
    self,
    user_id: str,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[Report], int]:
```

**Flow:**
```
ReportService
    ↓ calls
ReportRepository.list_reports(user_id, limit, offset)
    ↓ queries
Database (with pagination)
    ↓ returns
(List[Report], total_count)
```

**What happens:**
- Calls repository with pagination parameters
- Repository queries database with LIMIT/OFFSET
- Returns list of reports and total count
- Service just passes through (no business logic needed)

**Why this design:**
- Simple pass-through for listing
- Repository handles pagination
- Service can add filtering/sorting later if needed

---

### STEP 4: Search Reports

**Location:** `report_service.py`, `search_reports()` method

**Code:**
```python
async def search_reports(
    self,
    user_id: str,
    query: str,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[Report], int]:
```

**Flow:**
```
ReportService
    ↓ calls
ReportRepository.search_reports(user_id, query, limit, offset)
    ↓ queries
Database (with ILIKE search on name, question, description)
    ↓ returns
(List[Report], total_count)
```

**What happens:**
- Calls repository with search query
- Repository searches using SQL ILIKE
- Returns matching reports and total count

**Why this design:**
- Search logic in repository (SQL level)
- Service provides clean interface
- Can add advanced search later (full-text, etc.)

---

### STEP 5: Update Report

**Location:** `report_service.py`, `update_report()` method

**Code:**
```python
async def update_report(
    self,
    report_id: int,
    user_id: str,
    updated_report: Report,
) -> bool:
```

**Flow:**
```
ReportService
    ↓ validates
Check report exists and user has access (get_report)
    ↓ validates
Check report_id matches, user_id matches
    ↓ calls
ReportRepository.update_report()
    ↓ updates
Database
    ↓ returns
bool (success)
```

**What happens:**
1. **Authorization Check:** Verifies report exists and user has access
2. **Validation:** Ensures report_id and user_id match
3. **Update:** Calls repository to update
4. **Return:** Success status

**Why this design:**
- Service handles authorization (business rule)
- Service validates before update
- Repository handles data persistence

---

### STEP 6: Delete Report

**Location:** `report_service.py`, `delete_report()` method

**Code:**
```python
async def delete_report(
    self,
    report_id: int,
    user_id: str,
) -> bool:
```

**Flow:**
```
ReportService
    ↓ validates
Check report exists and user has access (get_report)
    ↓ calls
ReportRepository.delete_report()
    ↓ soft deletes
Database (sets status = 'deleted')
    ↓ returns
bool (success)
```

**What happens:**
- **Authorization Check:** Verifies report exists and user has access
- **Soft Delete:** Repository sets status to 'deleted' (not hard delete)
- **Return:** Success status

**Why soft delete:**
- Preserves data for audit trail
- Can restore if needed
- Better for production systems

---

### STEP 7: Execute Saved Report

**Location:** `report_service.py`, `execute_saved_report()` method

**Code:**
```python
async def execute_saved_report(
    self,
    report_id: int,
    user_id: str,
    max_rows: int = 500,
) -> Tuple[Report, List[Dict[str, Any]]]:
```

**Flow:**
```
ReportService
    ↓ validates
Check report exists and user has access (get_report)
    ↓ calls
ReportRepository.execute_saved_sql()
    ↓ executes
Database query (using saved SQL)
    ↓ returns
(Report, rows)
```

**What happens:**
- **Authorization Check:** Verifies report exists and user has access
- **Execute SQL:** Repository executes saved SQL query
- **Return:** Report metadata and query results

**Why this design:**
- Uses repository's execute method (direct SQL execution)
- Alternative: Could use QueryService, but that would regenerate SQL
- Direct execution is faster for saved queries

---

## Dependency Injection

ReportService receives dependencies in `__init__`:

```python
def __init__(
    self,
    report_repository: ReportRepository,  # ← Injected
):
```

### Why inject dependencies?

1. **TESTABILITY:**
   - Can pass mock repository in tests
   - Don't need real database for unit tests

2. **FLEXIBILITY:**
   - Can swap implementations easily
   - Use different repository for different environments

3. **CLEAR DEPENDENCIES:**
   - See exactly what service needs
   - No hidden dependencies

### Example usage:

```python
# In production:
from app.repositories.report_repository import AsyncReportRepository

report_repo = AsyncReportRepository()
report_service = ReportService(report_repo)

# In tests:
mock_report_repo = MockReportRepository()
report_service = ReportService(mock_report_repo)
```

---

## Layer Interactions

ReportService interacts with these layers:

1. **CORE LAYER** (`app/core/`)
   - Uses: `Report`, `QueryResult`
   - Uses: `ReportNotFoundError`, `UnauthorizedAccessError`
   - Why: Business domain models and exceptions

2. **REPOSITORIES LAYER** (`app/repositories/`)
   - Uses: `ReportRepository` (interface)
   - Why: Data access abstraction

3. **CONFIG LAYER** (`app/config/`)
   - Uses: `get_logger()`
   - Why: Logging configuration

**Service does NOT interact with:**
- API Layer (that's above services)
- Database directly (uses repository)
- QueryService (could, but doesn't need to for basic operations)

---

## Error Handling

Service handles errors at each step:

1. **Report Not Found:**
   - If report doesn't exist → `ReportNotFoundError`
   - Service logs warning and raises exception

2. **Unauthorized Access:**
   - If user tries to access another user's report → `UnauthorizedAccessError`
   - Service validates ownership before operations

3. **Validation Errors:**
   - If report data invalid → `ValueError` (from domain model)
   - Service validates before saving/updating

**Why raise exceptions?**
- Service focuses on business logic
- Error formatting is API layer's job
- Service logs for debugging

---

## Business Logic in Service

ReportService contains these business rules:

1. **Authorization:**
   - Users can only access their own reports
   - Validated before every operation

2. **Data Validation:**
   - Report ID must match on update
   - User ID cannot be changed
   - Domain model validates data structure

3. **Soft Delete:**
   - Reports are soft-deleted (status = 'deleted')
   - Not permanently removed

4. **Convenience Methods:**
   - `save_report_from_query()` - common use case
   - Encapsulates conversion logic

---

## Testing Strategy

### How to test ReportService:

1. **UNIT TESTS:**
   - Mock `ReportRepository` (return fake reports)
   - Test service logic only
   - Test authorization checks
   - Test validation logic

2. **INTEGRATION TESTS:**
   - Use real `ReportRepository` (real database)
   - Test full flow
   - Test database constraints

3. **WHAT TO TEST:**
   - ✅ Service saves reports correctly
   - ✅ Service retrieves reports correctly
   - ✅ Service lists reports with pagination
   - ✅ Service searches reports correctly
   - ✅ Service updates reports correctly
   - ✅ Service deletes reports correctly (soft delete)
   - ✅ Service executes saved SQL correctly
   - ✅ Service handles authorization correctly
   - ✅ Service handles errors correctly

---

## Summary

ReportService is the **MANAGER** of saved reports:

1. It orchestrates all report operations
2. It uses dependency injection for flexibility
3. It handles authorization and validation
4. It provides clean interface for API layer
5. It's easy to test (can mock repository)

**Key Features:**
- CRUD operations (Create, Read, Update, Delete)
- Search functionality
- Authorization checks
- Soft delete
- Convenience methods

**Next:** We'll build `SemanticService` to complete the Services Layer!


