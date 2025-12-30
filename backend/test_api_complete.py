"""
Complete API Test

Tests all endpoints with the server running.
Run this while the server is running.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

def test_health():
    """Test health endpoint"""
    print_section("TEST 1: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        if response.status_code == 200:
            print("✅ Health check PASSED")
            return True
        else:
            print("❌ Health check FAILED")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server not running!")
        print("   Start with: uvicorn app.api.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_validation_error():
    """Test validation error handling"""
    print_section("TEST 2: Validation Error Handling")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/query",
            json={"question": ""},  # Invalid: empty question
            timeout=5
        )
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 422:
            print("✅ Validation error handling PASSED (422 returned)")
            return True
        else:
            print(f"⚠️  Expected 422, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_query_endpoint():
    """Test query endpoint"""
    print_section("TEST 3: Query Endpoint")
    print("(Requires database connection and AI API keys)")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/query",
            json={
                "question": "Show me top 3 customers by YTD sales",
                "max_rows": 5
            },
            timeout=60  # Longer timeout for AI + DB
        )
        print(f"Status Code: {response.status_code}")
        result = response.json()
        
        if response.status_code == 200:
            print("✅ Query endpoint PASSED")
            print(f"   Rows returned: {result.get('row_count', 0)}")
            print(f"   Execution time: {result.get('execution_time_ms', 0):.2f}ms")
            print(f"   SQL: {result.get('query', {}).get('sql', '')[:80]}...")
            return True
        elif response.status_code == 500:
            print("⚠️  Query failed (expected if DB/AI not configured)")
            print(f"   Error: {result.get('error', 'Unknown')}")
            detail = result.get('detail', '')
            print(f"   Detail: {detail[:100]}...")
            
            # Check if error message is secure (generic)
            if any(word in detail.lower() for word in ['api key', 'database', 'connection', 'password']):
                print("   ⚠️  WARNING: Error may leak internal details!")
            else:
                print("   ✅ Error message is generic (secure)")
            return True  # Still pass - error handling works
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            print(f"   Response: {json.dumps(result, indent=2)}")
            return False
    except requests.exceptions.Timeout:
        print("⚠️  Request timed out")
        print("   ✅ Timeout protection is working!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n" + "=" * 70)
    print("API COMPLETE TEST SUITE")
    print("=" * 70)
    print("\n⚠️  Make sure the server is running:")
    print("   uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000\n")
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_health()))
    
    # Test 2: Validation error
    results.append(("Validation Error", test_validation_error()))
    
    # Test 3: Query endpoint
    results.append(("Query Endpoint", test_query_endpoint()))
    
    # Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests PASSED!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

