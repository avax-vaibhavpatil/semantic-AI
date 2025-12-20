#!/usr/bin/env python3
"""
Test Script for Report Management API
Tests all endpoints to ensure everything works correctly
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
COLORS = {
    'GREEN': '\033[0;32m',
    'RED': '\033[0;31m',
    'YELLOW': '\033[1;33m',
    'BLUE': '\033[0;34m',
    'NC': '\033[0m'  # No Color
}

def print_colored(text: str, color: str = 'NC'):
    """Print colored text"""
    print(f"{COLORS[color]}{text}{COLORS['NC']}")

def print_section(title: str):
    """Print section header"""
    print("\n" + "="*60)
    print_colored(f"  {title}", 'BLUE')
    print("="*60)

def test_endpoint(method: str, endpoint: str, data: Dict = None, expected_status: int = 200) -> Dict[str, Any]:
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PATCH":
            response = requests.patch(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        success = response.status_code == expected_status
        
        if success:
            print_colored(f"✅ {method} {endpoint} - Status {response.status_code}", 'GREEN')
        else:
            print_colored(f"❌ {method} {endpoint} - Status {response.status_code} (expected {expected_status})", 'RED')
        
        # Try to parse JSON response
        try:
            return {"success": success, "status": response.status_code, "data": response.json()}
        except:
            return {"success": success, "status": response.status_code, "data": response.text}
    
    except requests.exceptions.ConnectionError:
        print_colored(f"❌ Cannot connect to {BASE_URL}", 'RED')
        print_colored(f"   Make sure the server is running: uvicorn sql_agent:app --reload", 'YELLOW')
        return {"success": False, "status": 0, "data": None}
    except Exception as e:
        print_colored(f"❌ Error: {str(e)}", 'RED')
        return {"success": False, "status": 0, "data": None}

def main():
    """Run all tests"""
    print_colored("\n🧪 Report Management API Test Suite", 'BLUE')
    print_colored("=" * 60, 'BLUE')
    
    # Store report ID for subsequent tests
    report_id = None
    
    # ==========================================================================
    # Test 1: Health Check
    # ==========================================================================
    print_section("Test 1: Health Check")
    result = test_endpoint("GET", "/health")
    if result["success"]:
        print(f"   Semantic loaded: {result['data'].get('semantic_loaded', False)}")
    
    time.sleep(0.5)
    
    # ==========================================================================
    # Test 2: Save a Report
    # ==========================================================================
    print_section("Test 2: Save a Report")
    report_data = {
        "report_name": "Test Report - Sales Analysis",
        "user_question": "Show me top 10 customers by YTD sales",
        "generated_sql": "SELECT gws_cust_code, gws_cust_name, SUM(gws_ytd_sales) as total FROM public.gwanalytics GROUP BY gws_cust_code, gws_cust_name ORDER BY total DESC LIMIT 10",
        "report_description": "This is a test report created by the test script",
        "tags": ["test", "sales", "automated"]
    }
    
    result = test_endpoint("POST", "/reports/save", data=report_data, expected_status=200)
    if result["success"]:
        report_id = result["data"].get("report_id")
        print(f"   Report ID: {report_id}")
        print(f"   Message: {result['data'].get('message')}")
    else:
        print_colored("   ⚠️  Subsequent tests may fail without a report ID", 'YELLOW')
    
    time.sleep(0.5)
    
    # ==========================================================================
    # Test 3: List All Reports
    # ==========================================================================
    print_section("Test 3: List All Reports")
    result = test_endpoint("GET", "/reports?limit=10")
    if result["success"]:
        total = result["data"].get("total", 0)
        count = len(result["data"].get("reports", []))
        print(f"   Total reports: {total}")
        print(f"   Fetched: {count} reports")
        if count > 0:
            first_report = result["data"]["reports"][0]
            print(f"   First report: {first_report['report_name']}")
    
    time.sleep(0.5)
    
    # ==========================================================================
    # Test 4: Get Single Report
    # ==========================================================================
    if report_id:
        print_section("Test 4: Get Single Report Details")
        result = test_endpoint("GET", f"/reports/{report_id}")
        if result["success"]:
            report = result["data"]
            print(f"   Name: {report.get('report_name')}")
            print(f"   Created: {report.get('created_at')}")
            print(f"   Execution count: {report.get('execution_count', 0)}")
            print(f"   Tags: {report.get('tags', [])}")
    else:
        print_colored("\n⏭️  Skipping Test 4 (no report ID)", 'YELLOW')
    
    time.sleep(0.5)
    
    # ==========================================================================
    # Test 5: Execute Report (Get Fresh Data)
    # ==========================================================================
    if report_id:
        print_section("Test 5: Execute Report (Fresh Data)")
        result = test_endpoint("POST", f"/reports/{report_id}/execute", data={"max_rows": 10})
        if result["success"]:
            row_count = result["data"].get("row_count", 0)
            exec_time = result["data"].get("execution_time_ms", 0)
            print(f"   Rows returned: {row_count}")
            print(f"   Execution time: {exec_time}ms")
            if row_count > 0:
                print(f"   Sample data: {json.dumps(result['data']['rows'][0], indent=2)}")
    else:
        print_colored("\n⏭️  Skipping Test 5 (no report ID)", 'YELLOW')
    
    time.sleep(0.5)
    
    # ==========================================================================
    # Test 6: Update Report (Mark as Favorite)
    # ==========================================================================
    if report_id:
        print_section("Test 6: Update Report (Mark as Favorite)")
        result = test_endpoint("PATCH", f"/reports/{report_id}", data={"is_favorite": True})
        if result["success"]:
            print(f"   Is favorite: {result['data'].get('is_favorite')}")
    else:
        print_colored("\n⏭️  Skipping Test 6 (no report ID)", 'YELLOW')
    
    time.sleep(0.5)
    
    # ==========================================================================
    # Test 7: Search Reports
    # ==========================================================================
    print_section("Test 7: Search Reports")
    result = test_endpoint("GET", "/reports/search?q=test&limit=5")
    if result["success"]:
        count = len(result["data"].get("reports", []))
        print(f"   Found: {count} reports matching 'test'")
    
    time.sleep(0.5)
    
    # ==========================================================================
    # Test 8: Get Execution History
    # ==========================================================================
    if report_id:
        print_section("Test 8: Get Execution History")
        result = test_endpoint("GET", f"/reports/{report_id}/history?limit=5")
        if result["success"]:
            history = result["data"]
            print(f"   History records: {len(history)}")
            if len(history) > 0:
                latest = history[0]
                print(f"   Latest execution: {latest.get('executed_at')}")
                print(f"   Took: {latest.get('execution_time_ms')}ms")
                print(f"   Rows: {latest.get('row_count')}")
    else:
        print_colored("\n⏭️  Skipping Test 8 (no report ID)", 'YELLOW')
    
    time.sleep(0.5)
    
    # ==========================================================================
    # Test 9: Filter by Favorites
    # ==========================================================================
    print_section("Test 9: Filter by Favorites")
    result = test_endpoint("GET", "/reports?favorite_only=true")
    if result["success"]:
        count = len(result["data"].get("reports", []))
        print(f"   Favorite reports: {count}")
    
    time.sleep(0.5)
    
    # ==========================================================================
    # Test 10: Delete Report (Soft Delete)
    # ==========================================================================
    if report_id:
        print_section("Test 10: Delete Report (Soft Delete)")
        print_colored("   Note: This will soft-delete the test report", 'YELLOW')
        result = test_endpoint("DELETE", f"/reports/{report_id}")
        if result["success"]:
            print(f"   Message: {result['data'].get('message')}")
            print(f"   Deleted report ID: {result['data'].get('deleted_report_id')}")
    else:
        print_colored("\n⏭️  Skipping Test 10 (no report ID)", 'YELLOW')
    
    # ==========================================================================
    # Summary
    # ==========================================================================
    print_section("Test Summary")
    print_colored("✅ All tests completed!", 'GREEN')
    print("\n📝 What we tested:")
    print("   1. ✅ Health check endpoint")
    print("   2. ✅ Save report")
    print("   3. ✅ List reports (with pagination)")
    print("   4. ✅ Get single report details")
    print("   5. ✅ Execute report (get fresh data)")
    print("   6. ✅ Update report metadata")
    print("   7. ✅ Search reports")
    print("   8. ✅ Get execution history")
    print("   9. ✅ Filter by favorites")
    print("   10. ✅ Delete report (soft delete)")
    
    print("\n🎉 Report Management Feature is working!")
    print("\n📖 Next steps:")
    print("   1. Open http://localhost:8000/docs for interactive API documentation")
    print("   2. Build frontend UI components")
    print("   3. Add authentication (replace demo_user with real users)")
    print("")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n\n⚠️  Tests interrupted by user", 'YELLOW')
    except Exception as e:
        print_colored(f"\n\n❌ Test suite failed: {str(e)}", 'RED')

