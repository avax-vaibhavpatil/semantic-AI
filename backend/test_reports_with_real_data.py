"""
Test Report Routes with Real Data

This script:
1. Executes a real query using the query endpoint
2. Saves it as a report
3. Tests all report operations with real data from your database
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import httpx
from httpx import ASGITransport
from app.api.main import app
from app.api.dependencies import initialize_services


async def execute_real_query(client: httpx.AsyncClient, question: str):
    """Execute a real query and return the result"""
    print("=" * 70)
    print(f"STEP 1: Execute Real Query")
    print("=" * 70)
    print(f"Question: {question}\n")
    
    query_data = {
        "question": question,
        "max_rows": 100
    }
    
    response = await client.post("/api/v1/query", json=query_data)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Query executed successfully!")
        print(f"   SQL: {result.get('query', {}).get('sql', '')[:150]}...")
        print(f"   Rows returned: {result.get('row_count', 0)}")
        print(f"   Execution time: {result.get('execution_time_ms', 0):.2f}ms\n")
        return result
    else:
        print(f"❌ Query failed: {response.json()}")
        return None


async def save_real_report(client: httpx.AsyncClient, query_result: dict, report_name: str):
    """Save a real query result as a report"""
    print("=" * 70)
    print(f"STEP 2: Save Real Query as Report")
    print("=" * 70)
    print(f"Report Name: {report_name}\n")
    
    report_data = {
        "report_name": report_name,
        "user_question": query_result["query"]["question"],
        "generated_sql": query_result["query"]["sql"],
        "user_id": "real_user_test",
        "report_description": f"Real query: {query_result['query']['question']}",
        "tags": ["real-data", "test"],
        "is_favorite": True
    }
    
    response = await client.post("/api/v1/reports", json=report_data)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 201:
        report = response.json()["report"]
        print(f"✅ Report saved successfully!")
        print(f"   Report ID: {report['report_id']}")
        print(f"   Report Name: {report['report_name']}")
        print(f"   SQL: {report['generated_sql'][:150]}...\n")
        return report["report_id"]
    else:
        print(f"❌ Failed to save report: {response.json()}")
        return None


async def test_get_real_report(client: httpx.AsyncClient, report_id: int):
    """Test getting the real report"""
    print("=" * 70)
    print(f"TEST: Get Real Report (ID: {report_id})")
    print("=" * 70)
    
    response = await client.get(f"/api/v1/reports/{report_id}?user_id=real_user_test")
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        report = response.json()["report"]
        print(f"✅ Report retrieved successfully!")
        print(f"   Name: {report['report_name']}")
        print(f"   Question: {report['user_question']}")
        print(f"   SQL: {report['generated_sql'][:150]}...")
        print(f"   Created: {report['created_at']}\n")
        return True
    else:
        print(f"❌ Failed to get report: {response.json()}\n")
        return False


async def test_list_real_reports(client: httpx.AsyncClient):
    """Test listing real reports"""
    print("=" * 70)
    print(f"TEST: List Real Reports")
    print("=" * 70)
    
    response = await client.get("/api/v1/reports?user_id=real_user_test&limit=10")
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Reports listed successfully!")
        print(f"   Total reports: {result['total']}")
        print(f"   Reports returned: {len(result['reports'])}")
        for report in result['reports'][:3]:  # Show first 3
            print(f"   - {report['report_name']} (ID: {report['report_id']})")
        print()
        return True
    else:
        print(f"❌ Failed to list reports: {response.json()}\n")
        return False


async def test_update_real_report(client: httpx.AsyncClient, report_id: int):
    """Test updating the real report"""
    print("=" * 70)
    print(f"TEST: Update Real Report (ID: {report_id})")
    print("=" * 70)
    
    update_data = {
        "report_name": f"Updated: Real Query Report - {report_id}",
        "report_description": "Updated description for real data test",
        "tags": ["real-data", "test", "updated"],
        "is_favorite": False
    }
    
    response = await client.put(f"/api/v1/reports/{report_id}?user_id=real_user_test", json=update_data)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        report = response.json()["report"]
        print(f"✅ Report updated successfully!")
        print(f"   New Name: {report['report_name']}")
        print(f"   New Description: {report['report_description']}")
        print(f"   Tags: {report['tags']}\n")
        return True
    else:
        print(f"❌ Failed to update report: {response.json()}\n")
        return False


async def test_execute_real_report(client: httpx.AsyncClient, report_id: int):
    """Test executing the real saved report"""
    print("=" * 70)
    print(f"TEST: Execute Real Saved Report (ID: {report_id})")
    print("=" * 70)
    
    execute_data = {
        "max_rows": 50
    }
    
    response = await client.post(f"/api/v1/reports/{report_id}/execute?user_id=real_user_test", json=execute_data)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Report executed successfully!")
        print(f"   Report: {result['report']['report_name']}")
        print(f"   Rows returned: {result['row_count']}")
        print(f"   Sample data (first row): {result['rows'][0] if result['rows'] else 'No rows'}\n")
        return True
    else:
        error_detail = response.json().get('detail', 'Unknown error')
        print(f"⚠️  Execution returned {response.status_code}")
        print(f"   Error: {str(error_detail)[:200]}\n")
        return False


async def test_delete_real_report(client: httpx.AsyncClient, report_id: int):
    """Test deleting the real report"""
    print("=" * 70)
    print(f"TEST: Delete Real Report (ID: {report_id})")
    print("=" * 70)
    
    response = await client.delete(f"/api/v1/reports/{report_id}?user_id=real_user_test")
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✅ Report deleted successfully!")
        print(f"   Message: {response.json().get('message', 'Deleted')}\n")
        return True
    else:
        print(f"❌ Failed to delete report: {response.json()}\n")
        return False


async def main():
    """Run all tests with real data"""
    print("\n" + "=" * 70)
    print("REPORT ROUTES TEST WITH REAL DATA")
    print("=" * 70 + "\n")
    
    # Initialize services
    print("Initializing services...")
    initialize_services()
    print("✅ Services initialized\n")
    
    # Test questions (use real questions that work with your database)
    test_questions = [
        "Show me top 5 customers by YTD sales",
        "Show me total YTD sales by customer",
    ]
    
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        try:
            # Execute a real query
            query_result = await execute_real_query(client, test_questions[0])
            
            if not query_result:
                print("❌ Cannot proceed without a successful query")
                return
            
            # Save as report
            report_id = await save_real_report(
                client, 
                query_result, 
                f"Real Query Test - {test_questions[0][:50]}"
            )
            
            if not report_id:
                print("❌ Cannot proceed without saving a report")
                return
            
            # Test all operations with real report
            print("\n" + "=" * 70)
            print("TESTING ALL REPORT OPERATIONS WITH REAL DATA")
            print("=" * 70 + "\n")
            
            results = []
            
            # Test 1: Get report
            results.append(("Get Report", await test_get_real_report(client, report_id)))
            
            # Test 2: List reports
            results.append(("List Reports", await test_list_real_reports(client)))
            
            # Test 3: Update report
            results.append(("Update Report", await test_update_real_report(client, report_id)))
            
            # Test 4: Execute saved report
            results.append(("Execute Report", await test_execute_real_report(client, report_id)))
            
            # Test 5: Delete report (last, so we can test others first)
            results.append(("Delete Report", await test_delete_real_report(client, report_id)))
            
            # Summary
            print("=" * 70)
            print("TEST SUMMARY")
            print("=" * 70)
            
            passed = sum(1 for _, result in results if result)
            total = len(results)
            
            for test_name, result in results:
                status = "✅ PASSED" if result else "❌ FAILED"
                print(f"{status} - {test_name}")
            
            print(f"\nTotal: {passed}/{total} tests passed")
            
            if passed == total:
                print("\n🎉 ALL TESTS PASSED WITH REAL DATA!")
            else:
                print(f"\n⚠️  {total - passed} test(s) failed")
            
            print("=" * 70)
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

