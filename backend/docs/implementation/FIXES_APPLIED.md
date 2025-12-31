# Repository Layer: Errors, Fixes, and Solution Steps

## Summary
This document shows all errors encountered, the broken code, fixed code, and step-by-step solutions.

---

## Error #1: Semantic JSON File Not Found

### Error Message
```
SemanticLayerError: Semantic JSON file not found: backend/metadata/semantic.json
```

### BEFORE (Broken Code)
```python
# backend/app/repositories/semantic_repository.py
if semantic_json_path is None:
    settings = get_settings()
    semantic_json_path = settings.semantic_json_path  # "backend/metadata/semantic.json"

self.semantic_json_path = Path(semantic_json_path)  # ❌ Fails when CWD != project root
```

**Problem:** Relative path depends on current working directory (CWD). When running from `backend/` directory, path doesn't resolve.

### AFTER (Fixed Code)
```python
# Handle both absolute and relative paths
self.semantic_json_path = Path(semantic_json_path)
if not self.semantic_json_path.is_absolute():
    # Try from project root (calculated from __file__ location)
    project_root = Path(__file__).parent.parent.parent.parent
    # __file__ = backend/app/repositories/semantic_repository.py
    # parent.parent.parent.parent = project root
    
    potential_path = project_root / self.semantic_json_path
    if potential_path.exists():
        self.semantic_json_path = potential_path
    # Fallback: try from backend directory's parent
    elif not self.semantic_json_path.exists():
        backend_dir = Path(__file__).parent.parent.parent
        potential_path = backend_dir.parent / self.semantic_json_path
        if potential_path.exists():
            self.semantic_json_path = potential_path
```

### Solution Steps
1. **Identified Issue**: Path resolution depends on CWD, not file location
2. **Solution Strategy**: Use `__file__` to get actual file location, then calculate project root
3. **Implementation**: 
   - Check if path is absolute → use directly
   - If relative → calculate project root from `__file__`
   - Try project root + relative path
   - Fallback: try backend parent + relative path
4. **Result**: Works from any directory

---

## Error #2: SQL Parameter Binding - Missing `report_id`

### Error Message
```
sqlalchemy.exc.InvalidRequestError: A value is required for bind parameter 'report_id'
[SQL: SELECT * FROM analytics_llm.saved_reports 
      WHERE report_id = $1 AND user_id = $2 AND status != $3 LIMIT 1]
```

### BEFORE (Broken Code)
```python
# backend/app/repositories/report_repository.py - get_report()
async def get_report(self, report_id: int, user_id: str) -> Optional[Report]:
    rows = await execute_query(
        f"""
        SELECT *
        FROM {self.table_full}
        WHERE report_id = :report_id AND user_id = :user_id AND status != :deleted
        """,
        engine=self.engine,
        max_rows=1,
    )
    if not rows:
        return None
    return _row_to_report(rows[0])
```

**Problem:** `execute_query()` doesn't support parameterized queries. It only accepts raw SQL strings. The `:report_id`, `:user_id`, `:deleted` placeholders never get values.

### AFTER (Fixed Code)
```python
async def get_report(self, report_id: int, user_id: str) -> Optional[Report]:
    """Get a single report by ID and user_id."""
    async with self.engine.connect() as conn:
        result = await conn.execute(
            text(f"""
                SELECT *
                FROM {self.table_full}
                WHERE report_id = :report_id AND user_id = :user_id AND status != :deleted
                LIMIT 1
            """),
            {
                "report_id": report_id,
                "user_id": user_id,
                "deleted": REPORT_STATUS_DELETED,
            },
        )
        row = result.fetchone()
        if not row:
            return None
        return _row_to_report(dict(row._mapping))
```

### Solution Steps
1. **Identified Issue**: `execute_query()` is for dynamic SQL (AI-generated), not parameterized queries
2. **Root Cause**: Repository methods need parameterized queries for user input (IDs, filters)
3. **Solution Strategy**: Use direct connection with SQLAlchemy's `text()` and parameter dict
4. **Implementation**:
   - Replace `execute_query()` with `async with self.engine.connect() as conn:`
   - Wrap SQL with `text()` for parameterized queries
   - Pass parameters as dictionary: `{"report_id": report_id, ...}`
   - Use `result.fetchone()` and `dict(row._mapping)` for result handling
5. **Result**: Secure, parameterized queries that prevent SQL injection

---

## Error #3: SQL Parameter Binding - Missing `deleted` Parameter

### Error Message
```
sqlalchemy.exc.InvalidRequestError: A value is required for bind parameter 'deleted'
[SQL: UPDATE analytics_llm.saved_reports SET ...
      WHERE report_id = $7 AND user_id = $8 AND status != $9]
```

### BEFORE (Broken Code)
```python
# backend/app/repositories/report_repository.py - update_report()
async def update_report(self, report_id: int, user_id: str, updated: Report) -> bool:
    query = text(f"""
        UPDATE {self.table_full}
        SET report_name = :report_name, ...
        WHERE report_id = :report_id AND user_id = :user_id AND status != :deleted
    """)
    async with self.engine.begin() as conn:
        result = await conn.execute(
            query,
            {
                "report_name": updated.report_name,
                "report_description": updated.report_description,
                "tags": updated.tags[:MAX_TAGS_PER_REPORT] if updated.tags else [],
                "is_favorite": updated.is_favorite,
                "status": updated.status,
                "updated_at": datetime.utcnow(),
                "report_id": report_id,
                "user_id": user_id,
                # ❌ MISSING: "deleted": REPORT_STATUS_DELETED
            },
        )
        return result.rowcount > 0
```

**Problem:** SQL has `:deleted` placeholder in WHERE clause, but parameter dictionary doesn't include it.

### AFTER (Fixed Code)
```python
async def update_report(self, report_id: int, user_id: str, updated: Report) -> bool:
    query = text(f"""
        UPDATE {self.table_full}
        SET report_name = :report_name, ...
        WHERE report_id = :report_id AND user_id = :user_id AND status != :deleted
    """)
    async with self.engine.begin() as conn:
        result = await conn.execute(
            query,
            {
                "report_name": updated.report_name,
                "report_description": updated.report_description,
                "tags": updated.tags[:MAX_TAGS_PER_REPORT] if updated.tags else [],
                "is_favorite": updated.is_favorite,
                "status": updated.status,
                "updated_at": datetime.utcnow(),
                "report_id": report_id,
                "user_id": user_id,
                "deleted": REPORT_STATUS_DELETED,  # ✅ Added missing parameter
            },
        )
        return result.rowcount > 0
```

### Solution Steps
1. **Identified Issue**: Missing parameter in dictionary
2. **Root Cause**: WHERE clause uses `:deleted` but params dict didn't include it
3. **Solution**: Added `"deleted": REPORT_STATUS_DELETED` to parameter dictionary
4. **Result**: All parameters now bound correctly

---

## Error #4: `list_reports()` - Multiple Parameter Issues

### Error Message
```
sqlalchemy.exc.InvalidRequestError: A value is required for bind parameter 'user_id'
```

### BEFORE (Broken Code)
```python
async def list_reports(self, user_id: str, limit: int = 20, offset: int = 0):
    rows = await execute_query(
        f"""
        SELECT *
        FROM {self.table_full}
        WHERE user_id = :user_id AND status != :deleted
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
        """,
        engine=self.engine,
        max_rows=limit,
    )
    reports = [_row_to_report(r) for r in rows]

    total_rows = await execute_query(
        f"""
        SELECT COUNT(*) as total
        FROM {self.table_full}
        WHERE user_id = :user_id AND status != :deleted
        """,
        engine=self.engine,
        max_rows=1,
    )
    total = total_rows[0]["total"] if total_rows else 0
    return reports, total
```

**Problems:**
- Using `execute_query()` which doesn't support parameters
- Two separate calls (inefficient)
- No transaction guarantee

### AFTER (Fixed Code)
```python
async def list_reports(self, user_id: str, limit: int = 20, offset: int = 0):
    """List reports for a user with pagination."""
    async with self.engine.connect() as conn:
        # Get total count
        count_result = await conn.execute(
            text(f"""
                SELECT COUNT(*) as total
                FROM {self.table_full}
                WHERE user_id = :user_id AND status != :deleted
            """),
            {"user_id": user_id, "deleted": REPORT_STATUS_DELETED},
        )
        total = count_result.scalar_one()
        
        # Get reports
        result = await conn.execute(
            text(f"""
                SELECT *
                FROM {self.table_full}
                WHERE user_id = :user_id AND status != :deleted
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {
                "user_id": user_id,
                "deleted": REPORT_STATUS_DELETED,
                "limit": limit,
                "offset": offset,
            },
        )
        rows = [dict(row._mapping) for row in result]
        reports = [_row_to_report(r) for r in rows]
        
        return reports, total
```

### Solution Steps
1. **Identified Issue**: Same as Error #2 - wrong tool for parameterized queries
2. **Additional Issue**: Inefficient (two separate connections)
3. **Solution Strategy**: 
   - Use single connection context
   - Both queries use parameterized approach
   - Use `scalar_one()` for count (cleaner)
4. **Implementation**:
   - Single `async with self.engine.connect() as conn:` block
   - First query: COUNT with parameters
   - Second query: SELECT with parameters (including limit/offset)
   - Convert results properly: `dict(row._mapping)`
5. **Result**: Efficient, secure, single-connection queries

---

## Error #5: `search_reports()` - Same Parameter Issues

### BEFORE (Broken Code)
```python
async def search_reports(self, user_id: str, query: str, limit: int = 20, offset: int = 0):
    rows = await execute_query(
        f"""
        SELECT * FROM {self.table_full}
        WHERE user_id = :user_id AND status != :deleted
          AND (report_name ILIKE :q OR user_question ILIKE :q)
        LIMIT :limit OFFSET :offset
        """,
        engine=self.engine,
        max_rows=limit,
    )
    # ... similar COUNT query ...
```

**Problem:** Same as `list_reports()` - using `execute_query()` with parameters.

### AFTER (Fixed Code)
```python
async def search_reports(self, user_id: str, query: str, limit: int = 20, offset: int = 0):
    """Search reports by name, question, or description."""
    search_pattern = f"%{query}%"  # ✅ ILIKE pattern
    
    async with self.engine.connect() as conn:
        # Get total count
        count_result = await conn.execute(
            text(f"""
                SELECT COUNT(*) as total
                FROM {self.table_full}
                WHERE user_id = :user_id AND status != :deleted
                  AND (
                        report_name ILIKE :q
                     OR user_question ILIKE :q
                     OR COALESCE(report_description, '') ILIKE :q
                  )
            """),
            {
                "user_id": user_id,
                "deleted": REPORT_STATUS_DELETED,
                "q": search_pattern,  # ✅ Pattern with % wildcards
            },
        )
        total = count_result.scalar_one()
        
        # Get reports
        result = await conn.execute(
            text(f"""
                SELECT * FROM {self.table_full}
                WHERE user_id = :user_id AND status != :deleted
                  AND (
                        report_name ILIKE :q
                     OR user_question ILIKE :q
                     OR COALESCE(report_description, '') ILIKE :q
                  )
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {
                "user_id": user_id,
                "deleted": REPORT_STATUS_DELETED,
                "q": search_pattern,
                "limit": limit,
                "offset": offset,
            },
        )
        rows = [dict(row._mapping) for row in result]
        reports = [_row_to_report(r) for r in rows]
        
        return reports, total
```

### Solution Steps
1. **Identified Issue**: Same parameter binding problem
2. **Additional Feature**: Added search pattern (`%query%`) for ILIKE matching
3. **Solution**: Same pattern as `list_reports()` - parameterized queries with single connection
4. **Result**: Secure search with proper pattern matching

---

## Error #6: Deprecation Warning

### Error Message
```
DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal 
in a future version. Use timezone-aware objects to represent datetimes in UTC: 
datetime.datetime.now(datetime.UTC).
```

### BEFORE (Broken Code)
```python
from datetime import datetime

updated_at = datetime.utcnow()  # ❌ Deprecated in Python 3.12+
created_at = datetime.utcnow()  # ❌ Returns naive datetime (no timezone)
```

**Problem:** `datetime.utcnow()` returns naive datetime (no timezone info), deprecated in Python 3.12+.

### AFTER (Fixed Code)
```python
from datetime import datetime, timezone

updated_at = datetime.now(timezone.utc)  # ✅ Timezone-aware UTC
created_at = datetime.now(timezone.utc)  # ✅ Future-proof
```

### Solution Steps
1. **Identified Issue**: Deprecated function usage
2. **Root Cause**: Python 3.12+ requires timezone-aware datetimes
3. **Solution**: Replace `datetime.utcnow()` with `datetime.now(timezone.utc)`
4. **Result**: No warnings, timezone-aware, future-proof

---

## Complete Solution Summary

### All Methods Fixed

| Method | Issue | Solution |
|--------|-------|----------|
| `get_report()` | Parameter binding | Direct connection + `text()` + params dict |
| `list_reports()` | Parameter binding | Direct connection + two parameterized queries |
| `search_reports()` | Parameter binding | Direct connection + search pattern + params |
| `update_report()` | Missing `deleted` param | Added to params dict |
| `save_report()` | Already correct | No changes needed |
| `delete_report()` | Already correct | No changes needed |
| `execute_saved_sql()` | Already correct | Uses `execute_query()` (AI-generated SQL) |

### Key Pattern Applied

**For Repository Methods (User Input):**
```python
# ✅ CORRECT PATTERN
async with self.engine.connect() as conn:
    result = await conn.execute(
        text("SELECT ... WHERE col = :param"),
        {"param": value}  # ✅ Parameter dictionary
    )
    row = result.fetchone()
    return dict(row._mapping)
```

**For AI-Generated SQL:**
```python
# ✅ CORRECT PATTERN (different use case)
sql = ai_provider.generate_sql(question)  # AI generates complete SQL
rows = await execute_query(sql, max_rows=500)  # ✅ No parameters needed
```

### Testing Results

After all fixes:
```
✅ SemanticRepository: Loads semantic.json correctly
✅ ReportRepository: All CRUD operations work
✅ Parameterized queries: All execute successfully
✅ No deprecation warnings
✅ All tests pass
```

---

## Lessons Learned

1. **Path Resolution**: Always use `__file__` for relative paths, never CWD
2. **Parameterized Queries**: Use `conn.execute(text(), params)` for user input
3. **Dynamic SQL**: Use `execute_query()` only for AI-generated SQL
4. **Parameter Completeness**: Ensure all `:param` in SQL have matching dict keys
5. **Timezone Awareness**: Always use `datetime.now(timezone.utc)` in modern Python


