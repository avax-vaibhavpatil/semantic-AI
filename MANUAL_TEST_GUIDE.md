# Manual Test Guide - All Query Scenarios

This guide helps you manually test all query scenarios. Test them one by one in the frontend or via API.

## How to Test

### Option 1: Frontend (Recommended)
1. Open: `http://localhost:3000`
2. Type each query in the input box
3. Click "Ask" button
4. Check if SQL is generated correctly
5. Check if data is returned

### Option 2: API (Command Line)
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "YOUR_QUERY_HERE", "max_rows": 10}'
```

---

## 📋 Test Scenarios

### ✅ Category 1: Basic Queries

Test these simple queries first:

1. **show me total sales**
   - Expected: `SUM(gws_ytd_sales)`
   - Should return: 1 row with total

2. **total ytd sales**
   - Expected: `SUM(gws_ytd_sales)`

3. **give me all customer names**
   - Expected: `SELECT gws_cust_name`

4. **list all handler names**
   - Expected: `SELECT gws_hand_name`

5. **show me profit loss**
   - Expected: `gws_profit_loss`

6. **total outstanding amount**
   - Expected: `SUM(gws_os_amount)`

7. **count of customers**
   - Expected: `COUNT(*)`

---

### 🔍 Category 2: Filter Queries (WHERE)

Test queries with filters:

1. **show sales for handler 50149**
   - Expected: `WHERE gws_handled_by = '50149'`
   - Note: Should use quotes (dimension type)

2. **ytd sales where handled by is 50149**
   - Expected: `WHERE gws_handled_by = '50149'`

3. **customer name and sales for customer code 12345**
   - Expected: `WHERE gws_cust_code = '12345'`

4. **show me sales above 10000**
   - Expected: `WHERE gws_ytd_sales > 10000`
   - Note: No quotes (measure type)

5. **outstanding amount greater than 50000**
   - Expected: `WHERE gws_os_amount > 50000`

6. **profit loss less than zero**
   - Expected: `WHERE gws_profit_loss < 0`

---

### 📊 Category 3: Grouping Queries (GROUP BY)

Test aggregation with grouping:

1. **sales by handler name**
   - Expected: `GROUP BY gws_hand_name`
   - Should use `gws_hand_name` (not `gws_handled_by`)

2. **total sales grouped by customer name**
   - Expected: `GROUP BY gws_cust_name`

3. **ytd sales by handler**
   - Expected: `GROUP BY gws_hand_name`

4. **outstanding by customer code**
   - Expected: `GROUP BY gws_cust_code`

5. **profit loss by handler name**
   - Expected: `GROUP BY gws_hand_name`

6. **sales and budget by customer**
   - Expected: `GROUP BY gws_cust_name`

---

### 🏆 Category 4: Top-N Queries (ORDER BY + LIMIT)

Test top/bottom queries:

1. **top 5 handler by ytd sales**
   - Expected: `ORDER BY ... DESC LIMIT 5`
   - Should filter NULLs: `WHERE gws_hand_name IS NOT NULL`

2. **top 10 customers by sales**
   - Expected: `ORDER BY ... DESC LIMIT 10`

3. **show me top 5 handle by ytd sales**
   - Expected: `ORDER BY ... DESC LIMIT 5`
   - This is the query from your screenshot!

4. **bottom 5 customers by outstanding**
   - Expected: `ORDER BY ... ASC LIMIT 5`

5. **highest 3 sales**
   - Expected: `ORDER BY ... DESC LIMIT 3`

6. **lowest profit loss top 5**
   - Expected: `ORDER BY ... ASC LIMIT 5`

---

### 📅 Category 5: Date-Based Queries

Test various date formats:

1. **sales on 12 dec 2025**
   - Expected: `WHERE gws_date = '2025-12-12'`

2. **ytd sales as on 12-dec-2025**
   - Expected: `WHERE gws_date = '2025-12-12'`

3. **sales from 1 jan 2025 to 31 dec 2025**
   - Expected: `WHERE gws_date BETWEEN '2025-01-01' AND '2025-12-31'`

4. **sales from date 2025-01-01 to 2025-12-31**
   - Expected: `WHERE gws_date BETWEEN ...`

5. **sales for last 30 days**
   - Expected: `WHERE gws_date >= CURRENT_DATE - 30`

6. **sales for current month**
   - Expected: `WHERE gws_date >= DATE_TRUNC('month', CURRENT_DATE)`

7. **sales for december 2025**
   - Expected: `WHERE gws_date >= '2025-12-01' AND gws_date < '2026-01-01'`

---

### 🔗 Category 6: Complex Queries (Multiple clauses)

Test queries with multiple SQL clauses:

1. **sales by handler name where sales above 10000**
   - Expected: `GROUP BY ... HAVING SUM(...) > 10000`

2. **top 5 customers by sales where outstanding is zero**
   - Expected: `ORDER BY ... LIMIT 5 WHERE gws_os_amount = 0`

3. **handler wise total sales for date 12-dec-2025**
   - Expected: `GROUP BY ... WHERE gws_date = '2025-12-12'`

4. **customer name and sales where handled by 50149 and date is 12-dec-2025**
   - Expected: `WHERE ... AND ...`

5. **sales by handler having total sales greater than 50000**
   - Expected: `GROUP BY ... HAVING SUM(...) > 50000`

---

### ✏️ Category 7: Queries with TYPOS (Non-native English)

Test if system handles common typos:

1. **show me totl sales** (typo: totl → total)
   - Should work: Context is clear

2. **giv me customer name** (typo: giv → give)
   - Should work: Context is clear

3. **sales by handlar name** (typo: handlar → handler)
   - Should work: Aliases in semantic.json help

4. **top 5 handel by sales** (typo: handel → handle)
   - Should work: Aliases help

5. **ytd salse by customer** (typo: salse → sales)
   - Should work: Context is clear

6. **show me custmer code** (typo: custmer → customer)
   - Should work: Aliases help

7. **total outstandng amount** (typo: outstandng → outstanding)
   - Should work: Context is clear

8. **sales for handelr 50149** (typo: handelr → handler)
   - Should work: Aliases help

9. **profit los by handler** (typo: los → loss)
   - Should work: Context is clear

10. **show top 5 by ytd sal** (typo: sal → sales)
    - Should work: Context is clear

---

### 📝 Category 8: Grammar Mistakes (Non-native English)

Test if system handles grammar mistakes:

1. **show me sales** (missing article "the")
   - Should work: Intent is clear

2. **give total sales** (missing "me")
   - Should work: Intent is clear

3. **sales by handler name please** (extra "please")
   - Should work: Extra words ignored

4. **i want see customer name** (missing "to")
   - Should work: Intent is clear

5. **show sales where handler is 50149** ("is" instead of "=")
   - Should work: AI converts to SQL "="

6. **total sales group by customer** (missing "by" before group)
   - Should work: Intent is clear

7. **top 5 sales order by sales** (redundant but clear)
   - Should work: Redundancy handled

8. **customer name and their sales** (informal but clear)
   - Should work: Natural language

9. **show me handler name sales** (missing "and")
   - Should work: Intent is clear

10. **sales for date 12 dec** (missing year)
    - May need current year assumption

---

### ❓ Category 9: Ambiguous Queries

Test how system handles ambiguity:

1. **show me name**
   - Ambiguity: Which name? (customer/handler)
   - Expected: Should prefer `gws_cust_name` (preferred in semantic.json)

2. **total amount**
   - Ambiguity: Which amount? (sales/outstanding)
   - Expected: Should default to sales

3. **sales by code**
   - Ambiguity: Which code? (customer/handler)
   - Expected: Should prefer customer_code

4. **show me top sales**
   - Ambiguity: Top what?
   - Expected: Should default to top customers

5. **handler total**
   - Ambiguity: Total what?
   - Expected: Should default to total sales

---

### ⚠️ Category 10: Edge Cases

Test edge cases and error handling:

1. **show me everything**
   - Too vague
   - Expected: Should return error or ask for clarification

2. **all data**
   - Too vague
   - Expected: Should return error or ask for clarification

3. **sales**
   - Single word
   - Expected: Should work (context: show sales)

4. **total**
   - Single word
   - Expected: Should work (context: total sales)

5. **(empty query)**
   - No input
   - Expected: Should return error gracefully

---

## ✅ Success Criteria Checklist

After testing, verify:

- [ ] Basic queries work (100% success)
- [ ] Filter queries work (95%+ success)
- [ ] Grouping queries use correct columns (gws_hand_name not gws_handled_by)
- [ ] Top-N queries filter NULLs properly
- [ ] Date queries handle various formats
- [ ] Complex queries combine clauses correctly
- [ ] Typo queries work (80%+ success)
- [ ] Grammar mistakes are handled (85%+ success)
- [ ] Ambiguous queries use semantic.json preferences
- [ ] Edge cases fail gracefully with helpful errors

## 📊 Expected SQL Patterns

### Correct Column Selection
- ✅ "handler name" → `gws_hand_name` (not `gws_handled_by`)
- ✅ "customer name" → `gws_cust_name` (not `gws_cust_code`)
- ✅ "handler code" or "handled by" → `gws_handled_by`

### Correct Data Type Handling
- ✅ Dimension columns: `WHERE gws_handled_by = '50149'` (with quotes)
- ✅ Measure columns: `WHERE gws_ytd_sales > 10000` (no quotes)
- ✅ Date columns: `WHERE gws_date = '2025-12-12'` (with quotes)

### Correct NULL Handling
- ✅ Top-N queries: `WHERE column IS NOT NULL ORDER BY column DESC NULLS LAST`
- ✅ Aggregations: Don't over-filter (SUM/AVG ignore NULLs)

### No Hallucinated Values
- ❌ Don't create: `CASE WHEN gws_hand_name = 'Group Head'` (unless user explicitly asks)
- ✅ Create: `SUM(gws_ytd_sales)` (simple aggregation)

## 🐛 Common Issues to Watch For

1. **Wrong column selected**
   - Issue: Using `gws_handled_by` instead of `gws_hand_name`
   - Fix: Check semantic.json aliases

2. **Missing quotes in WHERE**
   - Issue: `WHERE gws_handled_by = 50149` (should be `'50149'`)
   - Fix: Check prompts.py data type handling

3. **Over-filtering NULLs**
   - Issue: `WHERE gws_ytd_sales IS NOT NULL AND gws_os_amount IS NOT NULL` (too many)
   - Fix: Check prompts.py NULL handling rules

4. **Hallucinated filter values**
   - Issue: `CASE WHEN gws_hand_name = 'Group Head'` (doesn't exist)
   - Fix: Check prompts.py anti-hallucination rules

5. **Date out of range**
   - Issue: Query returns 0 rows, no helpful message
   - Fix: Check sql_validator.py date validation

## 📝 Test Results Template

Create a file `TEST_RESULTS.md` and record:

```markdown
# Test Results - [Date]

## Category 1: Basic Queries
- [x] show me total sales - ✅ PASS
- [x] total ytd sales - ✅ PASS
- [ ] give me all customer names - ❌ FAIL (reason: ...)

## Category 2: Filter Queries
...

## Summary
- Total Tests: 50
- Passed: 45
- Failed: 5
- Success Rate: 90%
```

---

**Happy Testing! 🚀**

