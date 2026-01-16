#!/bin/bash
# Test queries on both tables via API

echo "=================================================================================="
echo "TESTING BACKEND: Both Tables (gwanalytics + stock_planning_data)"
echo "=================================================================================="

BASE_URL="http://localhost:8000"
USER_ID="test_user_123"

echo ""
echo "📍 TEST 1: Health Check"
echo "----------------------------------------------------------------------------------"
curl -s "$BASE_URL/health" | python3 -m json.tool
echo ""

echo "📍 TEST 2: gwanalytics Table Queries"
echo "----------------------------------------------------------------------------------"

echo ""
echo "Query 1: Show me total sales by customer"
curl -s -X POST "$BASE_URL/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"question": "Show me total sales by customer", "max_rows": 5}' | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"SQL: {data.get('query', {}).get('sql', 'N/A')[:150]}...\"); print(f\"Rows: {data.get('row_count', 0)}\"); print(f\"Time: {data.get('execution_time_ms', 0):.2f}ms\")"

echo ""
echo "Query 2: What are the top 5 customers by sales?"
curl -s -X POST "$BASE_URL/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"question": "What are the top 5 customers by sales?", "max_rows": 5}' | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"SQL: {data.get('query', {}).get('sql', 'N/A')[:150]}...\"); print(f\"Rows: {data.get('row_count', 0)}\"); print(f\"Time: {data.get('execution_time_ms', 0):.2f}ms\")"

echo ""
echo "📍 TEST 3: stock_planning_data Table Queries"
echo "----------------------------------------------------------------------------------"

echo ""
echo "Query 1: Show me stock levels by item"
curl -s -X POST "$BASE_URL/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"question": "Show me stock levels by item", "max_rows": 5}' | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"SQL: {data.get('query', {}).get('sql', 'N/A')[:150]}...\"); print(f\"Rows: {data.get('row_count', 0)}\"); print(f\"Time: {data.get('execution_time_ms', 0):.2f}ms\")"

echo ""
echo "Query 2: What items have low stock?"
curl -s -X POST "$BASE_URL/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"question": "What items have low stock?", "max_rows": 5}' | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"SQL: {data.get('query', {}).get('sql', 'N/A')[:150]}...\"); print(f\"Rows: {data.get('row_count', 0)}\"); print(f\"Time: {data.get('execution_time_ms', 0):.2f}ms\")"

echo ""
echo "Query 3: Show me reorder levels"
curl -s -X POST "$BASE_URL/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"question": "Show me reorder levels", "max_rows": 5}' | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"SQL: {data.get('query', {}).get('sql', 'N/A')[:150]}...\"); print(f\"Rows: {data.get('row_count', 0)}\"); print(f\"Time: {data.get('execution_time_ms', 0):.2f}ms\")"

echo ""
echo "📍 TEST 4: Table Selection Accuracy"
echo "----------------------------------------------------------------------------------"

echo ""
echo "Test 1: Should use gwanalytics for 'customer sales'"
curl -s -X POST "$BASE_URL/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"question": "Show me customer sales", "max_rows": 3}' | \
  python3 -c "import sys, json; data=json.load(sys.stdin); sql=data.get('query', {}).get('sql', '').lower(); print(f\"SQL contains 'gwanalytics' or 'gws_': {'gwanalytics' in sql or 'gws_' in sql}\"); print(f\"SQL: {sql[:120]}...\")"

echo ""
echo "Test 2: Should use stock_planning_data for 'stock level'"
curl -s -X POST "$BASE_URL/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"question": "What is the stock level?", "max_rows": 3}' | \
  python3 -c "import sys, json; data=json.load(sys.stdin); sql=data.get('query', {}).get('sql', '').lower(); print(f\"SQL contains 'stock_planning_data' or 'spd_': {'stock_planning_data' in sql or 'spd_' in sql}\"); print(f\"SQL: {sql[:120]}...\")"

echo ""
echo "=================================================================================="
echo "✅ Testing Complete"
echo "=================================================================================="








