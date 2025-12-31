#!/bin/bash

# Comprehensive API Test Suite using curl
# Tests all endpoints of the Auto Semantic BI Platform API

BASE_URL="http://localhost:8000"
TEST_USER_ID="test_user_curl_$(date +%s)"

echo "======================================================================"
echo "COMPREHENSIVE API TEST SUITE - Using curl"
echo "======================================================================"
echo ""
echo "Base URL: $BASE_URL"
echo "Test User ID: $TEST_USER_ID"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

# Function to print test result
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASSED${NC}: $2"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAILED${NC}: $2"
        ((FAILED++))
    fi
}

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_status=$4
    local test_name=$5
    
    echo -e "${BLUE}Testing: $test_name${NC}"
    echo "  $method $endpoint"
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method \
            "$BASE_URL$endpoint")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq "$expected_status" ]; then
        print_result 0 "$test_name"
        if [ -n "$body" ]; then
            echo "$body" | python3 -m json.tool 2>/dev/null | head -20 || echo "$body" | head -5
        fi
    else
        print_result 1 "$test_name (Expected $expected_status, got $http_code)"
        echo "Response: $body" | head -10
    fi
    echo ""
}

# ============================================================
# TEST 1: Health Check
# ============================================================
echo "======================================================================"
echo "TEST 1: Health Check"
echo "======================================================================"
test_endpoint "GET" "/health" "" 200 "Health Check Endpoint"
HEALTH_RESPONSE=$(curl -s "$BASE_URL/health")
echo "$HEALTH_RESPONSE" | python3 -m json.tool
echo ""

# ============================================================
# TEST 2: Query Endpoint
# ============================================================
echo "======================================================================"
echo "TEST 2: Query Endpoint (Natural Language to SQL)"
echo "======================================================================"

QUERY_DATA='{
    "question": "Show me top 5 customers by YTD sales",
    "max_rows": 10
}'

test_endpoint "POST" "/api/v1/query" "$QUERY_DATA" 200 "Execute Natural Language Query"

# Extract query result for later use
QUERY_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$QUERY_DATA" \
    "$BASE_URL/api/v1/query")

echo "Query Response:"
echo "$QUERY_RESPONSE" | python3 -m json.tool | head -30
echo ""

# Extract SQL for report saving (properly escape JSON)
GENERATED_SQL=$(echo "$QUERY_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data.get('query', {}).get('sql', '')))" 2>/dev/null)
echo "Generated SQL (first 100 chars): $(echo "$GENERATED_SQL" | python3 -c "import sys, json; print(json.load(sys.stdin)[:100])" 2>/dev/null)..."
echo ""

# ============================================================
# TEST 3: Save Report
# ============================================================
echo "======================================================================"
echo "TEST 3: Save Report"
echo "======================================================================"

# Use python to properly construct JSON with escaped SQL
SAVE_REPORT_DATA=$(python3 <<PYEOF
import json

data = {
    "report_name": "Top 5 Customers by YTD Sales",
    "user_question": "Show me top 5 customers by YTD sales",
    "generated_sql": ${GENERATED_SQL},
    "user_id": "$TEST_USER_ID",
    "report_description": "Test report created via curl",
    "tags": ["curl", "test", "sales"],
    "is_favorite": True
}

print(json.dumps(data))
PYEOF
)

test_endpoint "POST" "/api/v1/reports" "$SAVE_REPORT_DATA" 201 "Save New Report"

# Extract report ID
REPORT_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$SAVE_REPORT_DATA" \
    "$BASE_URL/api/v1/reports")

REPORT_ID=$(echo "$REPORT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('report', {}).get('report_id', ''))" 2>/dev/null)

if [ -n "$REPORT_ID" ] && [ "$REPORT_ID" != "None" ]; then
    echo -e "${GREEN}✅ Report saved with ID: $REPORT_ID${NC}"
    echo ""
else
    echo -e "${RED}❌ Failed to extract report ID${NC}"
    REPORT_ID=""
fi

# ============================================================
# TEST 4: Get Report
# ============================================================
echo "======================================================================"
echo "TEST 4: Get Report by ID"
echo "======================================================================"

if [ -n "$REPORT_ID" ] && [ "$REPORT_ID" != "None" ]; then
    test_endpoint "GET" "/api/v1/reports/$REPORT_ID?user_id=$TEST_USER_ID" "" 200 "Get Report by ID"
    
    GET_RESPONSE=$(curl -s "$BASE_URL/api/v1/reports/$REPORT_ID?user_id=$TEST_USER_ID")
    echo "Report Details:"
    echo "$GET_RESPONSE" | python3 -m json.tool | head -25
    echo ""
else
    echo -e "${YELLOW}⚠️  Skipping Get Report test (no report ID)${NC}"
    echo ""
fi

# ============================================================
# TEST 5: List Reports
# ============================================================
echo "======================================================================"
echo "TEST 5: List User Reports"
echo "======================================================================"

test_endpoint "GET" "/api/v1/reports?user_id=$TEST_USER_ID&limit=10&offset=0" "" 200 "List User Reports"

LIST_RESPONSE=$(curl -s "$BASE_URL/api/v1/reports?user_id=$TEST_USER_ID&limit=10&offset=0")
echo "Reports List:"
echo "$LIST_RESPONSE" | python3 -m json.tool | head -30
echo ""

# ============================================================
# TEST 6: Update Report
# ============================================================
echo "======================================================================"
echo "TEST 6: Update Report"
echo "======================================================================"

if [ -n "$REPORT_ID" ] && [ "$REPORT_ID" != "None" ]; then
    UPDATE_DATA='{
        "report_name": "Updated: Top 5 Customers by YTD Sales",
        "report_description": "Updated via curl test"
    }'
    
    test_endpoint "PUT" "/api/v1/reports/$REPORT_ID?user_id=$TEST_USER_ID" "$UPDATE_DATA" 200 "Update Report"
    
    UPDATED_RESPONSE=$(curl -s -X PUT \
        -H "Content-Type: application/json" \
        -d "$UPDATE_DATA" \
        "$BASE_URL/api/v1/reports/$REPORT_ID?user_id=$TEST_USER_ID")
    
    echo "Updated Report:"
    echo "$UPDATED_RESPONSE" | python3 -m json.tool | head -20
    echo ""
else
    echo -e "${YELLOW}⚠️  Skipping Update Report test (no report ID)${NC}"
    echo ""
fi

# ============================================================
# TEST 7: Execute Saved Report
# ============================================================
echo "======================================================================"
echo "TEST 7: Execute Saved Report"
echo "======================================================================"

if [ -n "$REPORT_ID" ] && [ "$REPORT_ID" != "None" ]; then
    EXECUTE_DATA='{
        "max_rows": 10
    }'
    
    test_endpoint "POST" "/api/v1/reports/$REPORT_ID/execute?user_id=$TEST_USER_ID" "$EXECUTE_DATA" 200 "Execute Saved Report"
    
    EXECUTE_RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$EXECUTE_DATA" \
        "$BASE_URL/api/v1/reports/$REPORT_ID/execute?user_id=$TEST_USER_ID")
    
    echo "Execution Result:"
    echo "$EXECUTE_RESPONSE" | python3 -m json.tool | head -30
    echo ""
else
    echo -e "${YELLOW}⚠️  Skipping Execute Report test (no report ID)${NC}"
    echo ""
fi

# ============================================================
# TEST 8: Error Handling - Invalid Query
# ============================================================
echo "======================================================================"
echo "TEST 8: Error Handling - Invalid Query"
echo "======================================================================"

INVALID_QUERY_DATA='{
    "question": "",
    "max_rows": 10
}'

test_endpoint "POST" "/api/v1/query" "$INVALID_QUERY_DATA" 422 "Invalid Query (Empty Question)"

# ============================================================
# TEST 9: Error Handling - Missing Field
# ============================================================
echo "======================================================================"
echo "TEST 9: Error Handling - Missing Required Field"
echo "======================================================================"

MISSING_FIELD_DATA='{
    "max_rows": 10
}'

test_endpoint "POST" "/api/v1/query" "$MISSING_FIELD_DATA" 422 "Missing Required Field (question)"

# ============================================================
# TEST 10: Error Handling - Non-existent Report
# ============================================================
echo "======================================================================"
echo "TEST 10: Error Handling - Non-existent Report"
echo "======================================================================"

test_endpoint "GET" "/api/v1/reports/99999?user_id=$TEST_USER_ID" "" 500 "Non-existent Report (should return error)"

# ============================================================
# TEST 11: Delete Report
# ============================================================
echo "======================================================================"
echo "TEST 11: Delete Report"
echo "======================================================================"

if [ -n "$REPORT_ID" ] && [ "$REPORT_ID" != "None" ]; then
    test_endpoint "DELETE" "/api/v1/reports/$REPORT_ID?user_id=$TEST_USER_ID" "" 200 "Delete Report"
    echo ""
else
    echo -e "${YELLOW}⚠️  Skipping Delete Report test (no report ID)${NC}"
    echo ""
fi

# ============================================================
# SUMMARY
# ============================================================
echo "======================================================================"
echo "TEST SUMMARY"
echo "======================================================================"
echo -e "${GREEN}✅ PASSED: $PASSED${NC}"
echo -e "${RED}❌ FAILED: $FAILED${NC}"
echo ""

TOTAL=$((PASSED + FAILED))
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! ($PASSED/$TOTAL)${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed ($FAILED/$TOTAL)${NC}"
    exit 1
fi

