# Test Queries for Natural Language to SQL System

Use these queries to test if the system correctly identifies and uses the right table. The table name in brackets `[table_name]` indicates which table should be selected.

## Stock Gateway (stock_gw) Queries  


1. **[stock_gw]** Show total stock quantity and total stock value by company and branch for the latest snapshot date.

2. **[stock_gw]** What is the total stock quantity above 4 years by branch code? Group by branch and order by total quantity descending.

3. **[stock_gw]** Display stock ageing breakdown showing quantities in 0-6 months, 6-12 months, 1-2 years, 2-3 years, 3-4 years, and above 4 years for company code 1.

4. **[stock_gw]** Show the top 10 items by total stock value. Include item code, branch code, and total value.              (working)

5. **[stock_gw]** Calculate total NOS count and total stock value grouped by godown code for the most recent date.

6. **[stock_gw]** What is the average stock quantity per item by company? Show company code and average quantity.

7. **[stock_gw]** Find items with stock value above 100000. Show item code, branch, godown, and stock value.

8. **[stock_gw]** Show stock quality breakdown: total drum quantity, good quantity, cut quantity, small quantity, and scrap quantity by branch.

## Stock Planning (stock_planning_data) Queries

show me items where there is requirement based on movment/stock level
show me item where thier is no req and pending PO
show me item their no stock level

9. **[stock_planning_data]** Show stock level, reorder level, and drum level for all items in company code 3 and branch code 24.

10. **[stock_planning_data]** What is the total stock level and average list price by company and branch?

11. **[stock_planning_data]** Display items that need reordering: show items where stock level is less than reorder level. Include item code, branch, stock level, and reorder level.

12. **[stock_planning_data]** Calculate total pending orders: sum of pending DI, ST, and DD by branch code/ item wise.

<!-- 13. **[stock_planning_data]** Show gross profit analysis: total gross profit and average gross profit by make (manufacturer). -->

14. **[stock_planning_data]** What is the issue average for 6 months and 12 months by item? Show item code and both averages.                   item code / catref/ product cod'

15. **[stock_planning_data]** Find items with stock above 6 months. Show item code, branch, and quantity above 6 months.

16. **[stock_planning_data]** Display stock transfer summary: total branch transfer out and stock transfer in by company code.

## GW Analytics (gwanalytics) Queries

17. **[gwanalytics]** Show year-to-date sales and budget by customer code. Order by sales descending.

18. **[gwanalytics]** What is the total YTD sales and last year YTD sales by handler code (salesperson)?

19. **[gwanalytics]** Display outstanding amounts above 180 days by customer. Show customer code and outstanding amount.

20. **[gwanalytics]** Calculate total sales in the last 90 days grouped by customer code.

21. **[gwanalytics]** Show profit and loss summary by handler code. Include handler code and total profit/loss.

22. **[gwanalytics]** What is the average YTD sales per customer? Show customer code and average sales.

23. **[gwanalytics]** Find customers with outstanding amount above 50000. Show customer code and outstanding amount.

24. **[gwanalytics]** Display sales performance: YTD sales, last year YTD sales, and last 90 days sales by handler code.

## Mixed/Complex Queries (Testing Table Selection)

25. **[stock_gw]** Show stock quantities by ageing buckets (0-6 months, 6-12 months, etc.) for items in company 1.

26. **[stock_planning_data]** Compare stock levels vs reorder levels: show items where current stock is below reorder point.

27. **[gwanalytics]** Show top 10 customers by year-to-date sales with their outstanding amounts.

28. **[stock_gw]** Calculate total stock value by quality type (drum, good, cut, small, scrap) for branch code 6.

29. **[stock_planning_data]** Show pending purchase orders breakdown: DI, ST, and DD pending quantities by branch.

30. **[gwanalytics]** Display sales trend: YTD sales vs last year YTD sales by handler, ordered by current year sales.

## Edge Cases and Validation

31. **[stock_gw]** Count total number of items by company and branch for the latest date.

32. **[stock_planning_data]** Show items with zero stock level. Include item code, branch, and make.

33. **[gwanalytics]** Find handlers with zero YTD sales. Show handler code and sales amount.

34. **[stock_gw]** What is the maximum stock value for any single item? Show item code, branch, and value.

35. **[stock_planning_data]** Calculate average issue average 6 months and 9 months by company code.

## How to Test

1. Copy any query from above (without the bracket notation)
2. Paste it into the frontend query interface
3. Check the generated SQL to verify:
   - Correct table is selected (check FROM clause)
   - Correct columns are used (check column prefixes: `stgw_*`, `spd_*`, `gws_*`)
   - No joins to non-existent tables
   - Proper aggregations and filters

## Expected Table Prefixes

- **stock_gw**: Columns start with `stgw_` (e.g., `stgw_item_code`, `stgw_branch_code`)
- **stock_planning_data**: Columns start with `spd_` (e.g., `spd_item_code`, `spd_branch_code`)
- **gwanalytics**: Columns start with `gws_` (e.g., `gws_cust_code`, `gws_ytd_sales`)

## Quick Test Checklist

- [ ] Query uses correct table (check FROM clause)
- [ ] Query uses correct column prefixes
- [ ] No joins to non-existent tables
- [ ] Proper NULL handling (COALESCE where needed)
- [ ] Correct data types in COALESCE (strings for VARCHAR, numbers for INTEGER/NUMERIC)
- [ ] ROUND function casts REAL to NUMERIC when needed
- [ ] Query executes without errors
- [ ] Results make sense for the question asked

