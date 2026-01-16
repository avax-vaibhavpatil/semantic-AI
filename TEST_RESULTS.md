# Random Test Results Summary

## Test Date
January 2025

## Overall Results
- **Total Tests**: 5 queries
- **Passed**: 1 (20%)
- **Failed**: 4 (80%)

## Issues Found

### 1. ❌ Wrong Table Selection
**Problem**: Even when explicitly mentioning "stock gateway table", the system selects `stock_planning_data` instead of `stock_gw`.

**Example**:
- Query: "Show total stock quantity by company from stock gateway table."
- Expected: `stock_gw` table with `stgw_*` columns
- Actual: `stock_planning_data` table with `spd_*` columns

**Root Cause**: The semantic layer is very large (~16,000 tokens), which may be causing the LLM to default to the first or most prominent table in the JSON.

**Impact**: High - Users cannot reliably query stock gateway data.

### 2. ❌ Groq Token Limits
**Problem**: Groq free tier has a 6000 tokens per minute (TPM) limit, but the semantic layer requires ~16,000 tokens.

**Error**: `Request too large for model 'llama-3.1-8b-instant'... Limit 6000, Requested 16527`

**Impact**: Medium - Groq cannot be used as a fallback for complex queries.

### 3. ❌ Claude Timeouts
**Problem**: Some queries are timing out after 30 seconds.

**Error**: `Query generation timed out. Please try again with a simpler question.`

**Impact**: Medium - Some queries cannot complete.

## Successful Tests

### ✅ Test 2: Stock Planning Data
- **Query**: "What is the average list price by company code?"
- **Table**: `stock_planning_data` ✅
- **Columns**: `spd_*` ✅
- **Result**: 1 row returned with correct data

## Recommendations

### Immediate Fixes
1. **Improve Table Selection**: 
   - Add table name matching at the beginning of the prompt
   - Prioritize explicit table mentions in user queries
   - Consider reducing semantic layer size or using table summaries

2. **Handle Groq Limits**:
   - Skip Groq for large semantic layers
   - Use Claude as primary provider
   - Consider semantic layer compression or summarization

3. **Increase Timeout**:
   - Consider increasing Claude timeout from 30s to 60s for complex queries
   - Or implement query complexity detection

### Long-term Solutions
1. **Semantic Layer Optimization**:
   - Create table summaries instead of full column details
   - Only include relevant columns per query
   - Implement semantic layer caching

2. **Table Selection Logic**:
   - Pre-process queries to detect table keywords
   - Use table name matching before sending to LLM
   - Implement table selection as a separate step

3. **Provider Strategy**:
   - Use Claude as primary (handles large contexts better)
   - Use Groq only for simple queries
   - Implement smart provider routing based on query complexity

## Test Queries Used

1. "Show total stock quantity by company from stock gateway table." → ❌ Wrong table
2. "What is the average list price by company code?" → ✅ Correct
3. "Show total YTD sales by customer code." → ❌ Groq token limit
4. "Display stock quantity above 4 years by branch from stock gateway." → ❌ Groq token limit
5. "Count items where stock level is less than reorder level." → ❌ Timeout

## Next Steps

1. Test with Claude-only provider (skip Groq)
2. Test with simplified semantic layer
3. Add explicit table name matching in query preprocessing
4. Test with longer timeout values





