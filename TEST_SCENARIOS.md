# Comprehensive Test Scenarios

This document lists all test scenarios for the Semantic AI BI Platform, including queries for non-native English speakers with typos and grammar mistakes.

## Test Categories

### 1. Basic Queries (Simple SELECT statements)

| # | Query | Expected SQL Elements |
|---|-------|---------------------|
| 1 | show me total sales | SUM(gws_ytd_sales) |
| 2 | total ytd sales | SUM(gws_ytd_sales) |
| 3 | give me all customer names | SELECT gws_cust_name |
| 4 | list all handler names | SELECT gws_hand_name |
| 5 | show me profit loss | gws_profit_loss |
| 6 | total outstanding amount | SUM(gws_os_amount) |
| 7 | count of customers | COUNT(*) |

### 2. Filter Queries (WHERE clauses)

| # | Query | Expected SQL Elements |
|---|-------|---------------------|
| 1 | show sales for handler 50149 | WHERE gws_handled_by = '50149' |
| 2 | ytd sales where handled by is 50149 | WHERE gws_handled_by = '50149' |
| 3 | customer name and sales for customer code 12345 | WHERE gws_cust_code = '12345' |
| 4 | show me sales above 10000 | WHERE gws_ytd_sales > 10000 |
| 5 | outstanding amount greater than 50000 | WHERE gws_os_amount > 50000 |
| 6 | profit loss less than zero | WHERE gws_profit_loss < 0 |

### 3. Grouping Queries (GROUP BY)

| # | Query | Expected SQL Elements |
|---|-------|---------------------|
| 1 | sales by handler name | GROUP BY gws_hand_name |
| 2 | total sales grouped by customer name | GROUP BY gws_cust_name |
| 3 | ytd sales by handler | GROUP BY gws_hand_name |
| 4 | outstanding by customer code | GROUP BY gws_cust_code |
| 5 | profit loss by handler name | GROUP BY gws_hand_name |
| 6 | sales and budget by customer | GROUP BY gws_cust_name |

### 4. Top-N Queries (ORDER BY + LIMIT)

| # | Query | Expected SQL Elements |
|---|-------|---------------------|
| 1 | top 5 handler by ytd sales | ORDER BY ... DESC LIMIT 5 |
| 2 | top 10 customers by sales | ORDER BY ... DESC LIMIT 10 |
| 3 | show me top 5 handle by ytd sales | ORDER BY ... DESC LIMIT 5 |
| 4 | bottom 5 customers by outstanding | ORDER BY ... ASC LIMIT 5 |
| 5 | highest 3 sales | ORDER BY ... DESC LIMIT 3 |
| 6 | lowest profit loss top 5 | ORDER BY ... ASC LIMIT 5 |

### 5. Date-Based Queries

| # | Query | Expected SQL Elements |
|---|-------|---------------------|
| 1 | sales on 12 dec 2025 | WHERE gws_date = '2025-12-12' |
| 2 | ytd sales as on 12-dec-2025 | WHERE gws_date = '2025-12-12' |
| 3 | sales from 1 jan 2025 to 31 dec 2025 | WHERE gws_date BETWEEN '2025-01-01' AND '2025-12-31' |
| 4 | sales from date 2025-01-01 to 2025-12-31 | WHERE gws_date BETWEEN |
| 5 | sales for last 30 days | WHERE gws_date >= CURRENT_DATE - 30 |
| 6 | sales for current month | WHERE gws_date >= DATE_TRUNC('month', CURRENT_DATE) |
| 7 | sales for december 2025 | WHERE gws_date >= '2025-12-01' AND gws_date < '2026-01-01' |

### 6. Complex Queries (Multiple clauses)

| # | Query | Expected SQL Elements |
|---|-------|---------------------|
| 1 | sales by handler name where sales above 10000 | GROUP BY ... HAVING SUM(...) > 10000 |
| 2 | top 5 customers by sales where outstanding is zero | ORDER BY ... LIMIT 5 WHERE gws_os_amount = 0 |
| 3 | handler wise total sales for date 12-dec-2025 | GROUP BY ... WHERE gws_date = '2025-12-12' |
| 4 | customer name and sales where handled by 50149 and date is 12-dec-2025 | WHERE ... AND ... |
| 5 | sales by handler having total sales greater than 50000 | GROUP BY ... HAVING SUM(...) > 50000 |

### 7. Queries with Typos (Non-native English)

| # | Query | Typo | Expected to Work? |
|---|-------|------|------------------|
| 1 | show me totl sales | totl → total | ✅ Yes (context) |
| 2 | giv me customer name | giv → give | ✅ Yes (context) |
| 3 | sales by handlar name | handlar → handler | ✅ Yes (aliases) |
| 4 | top 5 handel by sales | handel → handle | ✅ Yes (aliases) |
| 5 | ytd salse by customer | salse → sales | ✅ Yes (context) |
| 6 | show me custmer code | custmer → customer | ✅ Yes (aliases) |
| 7 | total outstandng amount | outstandng → outstanding | ✅ Yes (context) |
| 8 | sales for handelr 50149 | handelr → handler | ✅ Yes (aliases) |
| 9 | profit los by handler | los → loss | ✅ Yes (context) |
| 10 | show top 5 by ytd sal | sal → sales | ✅ Yes (context) |

### 8. Grammar Mistakes (Non-native English patterns)

| # | Query | Grammar Issue | Expected to Work? |
|---|-------|--------------|------------------|
| 1 | show me sales | Missing article "the" | ✅ Yes |
| 2 | give total sales | Missing "me" | ✅ Yes |
| 3 | sales by handler name please | Extra "please" | ✅ Yes |
| 4 | i want see customer name | Missing "to" | ✅ Yes |
| 5 | show sales where handler is 50149 | "is" instead of "=" | ✅ Yes (AI should convert) |
| 6 | total sales group by customer | Missing "by" before group | ✅ Yes |
| 7 | top 5 sales order by sales | Redundant but clear | ✅ Yes |
| 8 | customer name and their sales | Informal but clear | ✅ Yes |
| 9 | show me handler name sales | Missing "and" | ✅ Yes |
| 10 | sales for date 12 dec | Missing year | ⚠️ May need current year |

### 9. Ambiguous Queries

| # | Query | Ambiguity | Expected Behavior |
|---|-------|-----------|------------------|
| 1 | show me name | Which name? (customer/handler) | Should prefer based on context or ask |
| 2 | total amount | Which amount? (sales/outstanding) | Should default to sales or ask |
| 3 | sales by code | Which code? (customer/handler) | Should prefer customer_code |
| 4 | show me top sales | Top what? | Should default to top customers |
| 5 | handler total | Total what? | Should default to total sales |

### 10. Edge Cases

| # | Query | Issue | Expected Behavior |
|---|-------|-------|------------------|
| 1 | show me everything | Too vague | Should return error or ask for clarification |
| 2 | all data | Too vague | Should return error or ask for clarification |
| 3 | sales | Single word | Should work (context: show sales) |
| 4 | total | Single word | Should work (context: total sales) |
| 5 | (empty query) | No input | Should return error gracefully |

## Testing Instructions

### Run Automated Test Suite

```bash
cd backend
source venv/bin/activate
python3 test_comprehensive_queries.py
```

### Manual Testing via Frontend

1. Start backend: `cd backend && source venv/bin/activate && uvicorn sql_agent:app --host 0.0.0.0 --port 8000`
2. Start frontend: `cd frontend && npm run dev`
3. Open browser: `http://localhost:3000`
4. Test each query from the scenarios above

### Manual Testing via API

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "show me top 5 handle by ytd sales", "max_rows": 10}'
```

## Expected Behaviors

### ✅ Should Work
- Queries with typos (if context is clear)
- Queries with grammar mistakes (if intent is clear)
- Ambiguous queries (should use semantic.json preferences)
- Date queries in various formats
- Complex multi-clause queries

### ⚠️ Should Show Warning
- Queries returning 0 rows (with helpful message)
- Queries with date out of range
- Queries with over-restrictive NULL filters

### ❌ Should Fail Gracefully
- Empty queries
- Queries that are too vague
- Queries referencing non-existent columns
- Queries with SQL injection attempts

## Success Criteria

- **Basic queries**: 100% success rate
- **Filter queries**: 95%+ success rate
- **Grouping queries**: 95%+ success rate
- **Top-N queries**: 90%+ success rate (with NULL handling)
- **Date queries**: 90%+ success rate
- **Complex queries**: 85%+ success rate
- **Typo queries**: 80%+ success rate (context-dependent)
- **Grammar mistakes**: 85%+ success rate
- **Ambiguous queries**: 70%+ success rate (preference-based)
- **Edge cases**: Should fail gracefully with helpful errors

## Notes for Non-Native English Speakers

The system is designed to handle:
- **Typos**: Common misspellings (totl → total, salse → sales)
- **Grammar mistakes**: Missing articles, prepositions, verb forms
- **Informal language**: "give me", "show me", "i want"
- **Mixed languages**: Some Hindi/regional words may work if context is clear
- **Abbreviations**: "ytd", "os", "cust" are recognized

## Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Query returns 0 rows | Check date range, relax NULL filters |
| Wrong column selected | Update semantic.json aliases |
| Date format not recognized | Use standard formats: YYYY-MM-DD or "DD-MMM-YYYY" |
| Ambiguous query | Be more specific (e.g., "customer name" vs "handler name") |

