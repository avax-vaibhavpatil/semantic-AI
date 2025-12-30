# Test Errors Diagnosis - QueryService and ReportService

This document explains the errors we encountered during testing and how we fixed them.

---

## Error 1: QueryRequest - Unexpected `user_id` Argument

### Error Message:
```
TypeError: QueryRequest.__init__() got an unexpected keyword argument 'user_id'
```

### Location:
- File: `backend/app/services/test_query_and_report_services.py`
- Line: ~75
- Function: `test_query_and_report_services()`

### Root Cause:
The test was trying to pass `user_id` to `QueryRequest`, but `QueryRequest` doesn't have a `user_id` field.

**QueryRequest Definition:**
```python
@dataclass
class QueryRequest:
    question: str
    max_rows: int = 500
    dialect: Optional[str] = None
    # ❌ NO user_id field!
```

### Why This Happened:
- `user_id` is needed for **ReportService** (to save reports)
- But `QueryRequest` is just for the query itself (question + SQL generation)
- `user_id` is only needed when **saving** the query result as a report

### Solution:
Removed `user_id` from `QueryRequest` initialization:

**Before (❌ Wrong):**
```python
query_request = QueryRequest(
    question="Show me top 5 customers by YTD sales",
    user_id=test_user_id,  # ❌ This field doesn't exist
)
```

**After (✅ Correct):**
```python
query_request = QueryRequest(
    question="Show me top 5 customers by YTD sales",
    max_rows=100,  # ✅ Valid field
)
```

### Design Explanation:
- **QueryRequest**: Represents the user's question (no user context needed)
- **ReportService.save_report_from_query()**: Takes `user_id` separately when saving
- This separation keeps QueryRequest focused on the query itself

---

## Error 2: Claude Model Not Found (404)

### Error Message:
```
anthropic.NotFoundError: Error code: 404 - {
    'type': 'error', 
    'error': {
        'type': 'not_found_error', 
        'message': 'model: claude-3-sonnet-20240229'
    }
}
```

### Location:
- File: `backend/app/infrastructure/ai/providers/claude_provider.py`
- Line: ~38
- Function: `generate_sql()`

### Root Cause:
The Claude provider was trying to use `claude-3-sonnet-20240229`, which:
1. Doesn't exist or is not accessible with the provided API key
2. May have been set via environment variable `ANTHROPIC_MODEL`
3. The default in code is `claude-3-haiku-20240307`, but env var overrode it

### Why This Happened:
1. **Environment Variable Override**: If `ANTHROPIC_MODEL` was set to `claude-3-sonnet-20240229` in `.env` or environment
2. **API Key Tier**: The API key might not have access to Sonnet model
3. **Model Availability**: Sonnet model might not be available for this API key tier

### Solution:
Explicitly set the model to Haiku (which we know works) in the test:

**Before (❌ Wrong):**
```python
claude_provider = ClaudeProvider()  # Uses env var or default
# If ANTHROPIC_MODEL env var was set to wrong model, it fails
```

**After (✅ Correct):**
```python
claude_provider = ClaudeProvider(model="claude-3-haiku-20240307")
# Explicitly use Haiku model that we know works
```

### Design Explanation:
- **ClaudeProvider** checks: `model or os.environ.get("ANTHROPIC_MODEL", "claude-3-haiku-20240307")`
- If `ANTHROPIC_MODEL` env var exists, it overrides the default
- By passing `model` explicitly, we bypass the env var

### Prevention:
1. **In Production**: Set `ANTHROPIC_MODEL` env var to a valid model
2. **In Tests**: Explicitly pass the model to avoid env var issues
3. **Fallback**: The router will try Groq if Claude fails (retryable error)

---

## Error 3: Missing Exception - UnauthorizedAccessError

### Error Message:
```
ImportError: cannot import name 'UnauthorizedAccessError' from 'app.core.exceptions'
```

### Location:
- File: `backend/app/services/report_service.py`
- Line: 25
- Import statement

### Root Cause:
`ReportService` was trying to import `UnauthorizedAccessError`, but it didn't exist in `app.core.exceptions`.

### Why This Happened:
- `ReportService` was created with this import
- But `UnauthorizedAccessError` wasn't defined in the exceptions module
- We had `ReportAccessDeniedError` but not `UnauthorizedAccessError`

### Solution:
Added `UnauthorizedAccessError` to `app.core.exceptions`:

**Before (❌ Missing):**
```python
# app/core/exceptions.py
class ReportAccessDeniedError(DomainException):
    """Raised when user doesn't have access to a report"""
    pass
# ❌ No UnauthorizedAccessError
```

**After (✅ Added):**
```python
# app/core/exceptions.py
class ReportAccessDeniedError(DomainException):
    """Raised when user doesn't have access to a report"""
    pass

class UnauthorizedAccessError(DomainException):
    """Raised when user tries to access/modify resource they don't own"""
    pass
```

### Design Explanation:
- **ReportAccessDeniedError**: For access control (permissions)
- **UnauthorizedAccessError**: For ownership validation (user owns the resource)
- Both are needed for different scenarios

---

## Summary of Fixes

| Error | Root Cause | Solution | Status |
|-------|------------|----------|--------|
| **QueryRequest user_id** | Field doesn't exist | Removed `user_id` from QueryRequest | ✅ Fixed |
| **Claude Model 404** | Wrong model in env var | Explicitly use Haiku model | ✅ Fixed |
| **UnauthorizedAccessError** | Exception not defined | Added to exceptions.py | ✅ Fixed |

---

## Lessons Learned

1. **Check Domain Models**: Always verify what fields a domain model has before using it
2. **Environment Variables**: Be aware that env vars can override defaults
3. **Exception Completeness**: Ensure all exceptions used in code are defined
4. **Test Isolation**: Explicitly set dependencies in tests to avoid env var issues

---

## Testing Best Practices

1. **Explicit Dependencies**: Pass dependencies explicitly in tests (don't rely on env vars)
2. **Model Validation**: Verify domain models match their usage
3. **Exception Coverage**: Ensure all custom exceptions are defined
4. **Error Messages**: Clear error messages help diagnose issues quickly

---

## Current Status

✅ **All errors fixed**
✅ **All tests passing**
✅ **Services working correctly together**

Ready to move to API layer! 🚀

