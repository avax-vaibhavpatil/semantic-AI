# Fix for 500 Internal Server Error

## Problem
When querying "Show total stock quantity and total stock value by company and branch for the latest snapshot date", the API returns a 500 error because:
1. The LLM chooses the wrong table (`stock_planning_data` instead of `stock_gw`)
2. It tries to use a non-existent column (`spd_stock_lvl_value`)
3. The database error wasn't being properly converted to a user-friendly error

## Solution Applied

### 1. Improved Error Handling
- Added proper exception handling in `query_service.py` to convert database errors to `SQLExecutionError`
- Database errors now return user-friendly messages instead of generic 500 errors

### 2. Enhanced System Prompt
- Added clearer guidance about table selection
- Added specific instructions about column prefixes (stgw_*, spd_*, gws_*)
- Added guidance to prefer `stock_gw` table when user mentions "stock gateway" or "gateway"

## How to Use

### Option 1: Be More Specific (Recommended)
When querying stock gateway data, explicitly mention "stock gateway" or "stock_gw":

```
✅ Good: "Show total stock quantity and total stock value by company and branch for the latest snapshot date from stock gateway table"
✅ Good: "Show total stock quantity and total stock value by company and branch for the latest snapshot date from stock_gw"
```

### Option 2: Use Column Names
You can also use the specific column prefixes to help the LLM choose the right table:

```
✅ Good: "Show stgw_stock_lvl and stgw_stock_lvl_value by stgw_company_code and stgw_branch_code for the latest stgw_date"
```

## Testing

Test the fix:
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Show total stock quantity and total stock value by company and branch for the latest snapshot date from stock gateway table", "max_rows": 10}'
```

## Next Steps

1. **Restart the API server** to pick up the changes:
   ```bash
   # Stop the current server (Ctrl+C)
   # Then restart:
   cd backend
   source venv/bin/activate
   uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Test the original query** - it should now return a better error message if the LLM still chooses the wrong table

3. **Consider improving the semantic layer** - Add better table descriptions to help the LLM choose the right table automatically

