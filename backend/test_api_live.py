"""
Live API Test

Tests the API by starting the server and making actual HTTP requests.
"""

import subprocess
import time
import requests
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_api():
    """Test API endpoints"""
    print("=" * 70)
    print("Live API Testing")
    print("=" * 70)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Health Check
    print("\n1. Testing Health Check Endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        if response.status_code == 200:
            print("   ✅ Health check passed!")
        else:
            print("   ❌ Health check failed!")
    except requests.exceptions.ConnectionError:
        print("   ❌ Server not running. Start with: uvicorn app.api.main:app --reload")
        return
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Validation Error
    print("\n2. Testing Validation Error Handling...")
    try:
        response = requests.post(
            f"{base_url}/api/v1/query",
            json={"question": ""},  # Invalid: empty question
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        if response.status_code == 422:
            print("   ✅ Validation error handling works!")
        else:
            print(f"   ⚠️  Expected 422, got {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Query Endpoint (requires DB and AI)
    print("\n3. Testing Query Endpoint...")
    print("   (Requires database connection and AI API keys)")
    try:
        response = requests.post(
            f"{base_url}/api/v1/query",
            json={
                "question": "Show me top 3 customers by YTD sales",
                "max_rows": 5
            },
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        
        if response.status_code == 200:
            print("   ✅ Query successful!")
            print(f"   Rows: {result.get('row_count', 0)}")
            print(f"   Execution time: {result.get('execution_time_ms', 0):.2f}ms")
        elif response.status_code == 500:
            print("   ⚠️  Query failed (check error message)")
            print(f"   Error: {result.get('error', 'Unknown')}")
            print(f"   Detail: {result.get('detail', 'N/A')}")
            # Check if error message is generic (secure)
            detail = result.get('detail', '')
            if 'API key' in detail or 'database' in detail.lower():
                print("   ⚠️  WARNING: Error message may leak internal details!")
            else:
                print("   ✅ Error message is generic (secure)")
        else:
            print(f"   Status: {response.status_code}")
            print(f"   Response: {json.dumps(result, indent=2)}")
    except requests.exceptions.Timeout:
        print("   ⚠️  Request timed out (timeout protection working?)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 70)
    print("Testing Complete!")
    print("=" * 70)
    print("\nTo start the server manually:")
    print("  cd backend")
    print("  uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    print("\n⚠️  Make sure the server is running first!")
    print("   Start with: uvicorn app.api.main:app --reload\n")
    time.sleep(2)
    test_api()

