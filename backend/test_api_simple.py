#!/usr/bin/env python3
"""Simple API test script"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"
USER_ID = "test_user"

def test_query(question, expected_table=None):
    """Test a single query"""
    print(f"\n📝 Query: {question}")
    print("-" * 80)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/query",
            headers={
                "Content-Type": "application/json",
                "X-User-Id": USER_ID
            },
            json={
                "question": question,
                "max_rows": 5
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
        
        data = response.json()
        sql = data.get("query", {}).get("sql", "")
        row_count = data.get("row_count", 0)
        exec_time = data.get("execution_time_ms", 0)
        
        print(f"✅ SQL: {sql[:150]}...")
        print(f"✅ Rows: {row_count}")
        print(f"✅ Time: {exec_time:.2f}ms")
        
        if expected_table:
            sql_lower = sql.lower()
            if expected_table == "gwanalytics":
                uses_correct = "gwanalytics" in sql_lower or "gws_" in sql_lower
            else:
                uses_correct = "stock_planning_data" in sql_lower or "spd_" in sql_lower
            
            if uses_correct:
                print(f"✅ Correct table: {expected_table}")
            else:
                print(f"❌ Wrong table! Expected: {expected_table}")
                return False
        
        if row_count > 0:
            rows = data.get("rows", [])
            if rows:
                print(f"📊 Sample row: {rows[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 80)
    print("BACKEND TEST: Both Tables")
    print("=" * 80)
    
    # Health check
    print("\n📍 TEST 1: Health Check")
    print("-" * 80)
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Backend is running: {response.json()}")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("Make sure backend is running: uvicorn app.api.main:app --host 0.0.0.0 --port 8000")
        return
    
    # Test gwanalytics queries
    print("\n" + "=" * 80)
    print("TEST 2: gwanalytics Table Queries")
    print("=" * 80)
    
    gwanalytics_tests = [
        ("Show me total sales by customer", "gwanalytics"),
        ("What are the top 5 customers by sales?", "gwanalytics"),
    ]
    
    gwanalytics_results = []
    for question, table in gwanalytics_tests:
        result = test_query(question, table)
        gwanalytics_results.append(result)
    
    # Test stock_planning queries
    print("\n" + "=" * 80)
    print("TEST 3: stock_planning_data Table Queries")
    print("=" * 80)
    
    stock_tests = [
        ("Show me stock levels by item", "stock_planning_data"),
        ("What items have low stock?", "stock_planning_data"),
        ("Show me reorder levels", "stock_planning_data"),
    ]
    
    stock_results = []
    for question, table in stock_tests:
        result = test_query(question, table)
        stock_results.append(result)
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    gwanalytics_pass = sum(gwanalytics_results)
    stock_pass = sum(stock_results)
    total_pass = gwanalytics_pass + stock_pass
    total_tests = len(gwanalytics_results) + len(stock_results)
    
    print(f"\n✅ gwanalytics queries: {gwanalytics_pass}/{len(gwanalytics_results)} passed")
    print(f"✅ stock_planning queries: {stock_pass}/{len(stock_results)} passed")
    print(f"\n📊 Overall: {total_pass}/{total_tests} tests passed")
    
    if total_pass == total_tests:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total_tests - total_pass} test(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    main()










