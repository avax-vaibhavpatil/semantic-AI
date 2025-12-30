"""
Test API Endpoints

Quick test script to verify the API is working correctly.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import httpx
from app.api.main import app
from fastapi.testclient import TestClient


def test_health_endpoint():
    """Test health check endpoint"""
    print("=" * 70)
    print("TEST 1: Health Check Endpoint")
    print("=" * 70)
    
    # Initialize services manually (TestClient doesn't trigger startup events)
    from app.api.dependencies import initialize_services
    initialize_services()
    
    client = TestClient(app)
    response = client.get("/health")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200, "Health check should return 200"
    assert response.json()["status"] == "ok", "Status should be 'ok'"
    print("✅ Health check passed!\n")


def test_query_endpoint():
    """Test query endpoint"""
    print("=" * 70)
    print("TEST 2: Query Endpoint")
    print("=" * 70)
    
    # Initialize services manually
    from app.api.dependencies import initialize_services
    initialize_services()
    
    client = TestClient(app)
    
    # Test query request
    request_data = {
        "question": "Show me top 5 customers by YTD sales",
        "max_rows": 10
    }
    
    print(f"Request: {request_data}")
    print("Sending request...")
    
    try:
        response = client.post("/api/v1/query", json=request_data)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Query successful!")
            print(f"   Rows returned: {result.get('row_count', 0)}")
            print(f"   Execution time: {result.get('execution_time_ms', 0):.2f}ms")
            print(f"   SQL: {result.get('query', {}).get('sql', '')[:100]}...")
        else:
            print(f"❌ Query failed!")
            print(f"   Response: {response.json()}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_error_handling():
    """Test error handling"""
    print("\n" + "=" * 70)
    print("TEST 3: Error Handling")
    print("=" * 70)
    
    # Initialize services manually
    from app.api.dependencies import initialize_services
    initialize_services()
    
    client = TestClient(app)
    
    # Test invalid request (empty question)
    print("Testing invalid request (empty question)...")
    response = client.post("/api/v1/query", json={"question": ""})
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Should return 422 (validation error)
    assert response.status_code == 422, "Should return 422 for validation error"
    print("✅ Error handling works correctly!\n")


def test_dependency_initialization():
    """Test that services are initialized"""
    print("=" * 70)
    print("TEST 4: Dependency Initialization Check")
    print("=" * 70)
    
    from app.api.dependencies import get_query_service
    
    try:
        service = get_query_service()
        print(f"✅ QueryService retrieved successfully!")
        print(f"   Service type: {type(service).__name__}")
    except RuntimeError as e:
        print(f"❌ Services not initialized: {e}")
        print("   Note: Services should be initialized at app startup")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Testing API Endpoints")
    print("=" * 70 + "\n")
    
    # Test health endpoint
    test_health_endpoint()
    
    # Test dependency initialization
    test_dependency_initialization()
    
    # Test error handling
    test_error_handling()
    
    # Test query endpoint (requires database and AI keys)
    print("\n" + "⚠️  Note: Query endpoint test requires:")
    print("   - Database connection (DATABASE_URL)")
    print("   - AI API keys (ANTHROPIC_API_KEY or GROQ_API_KEY)")
    print("   - Semantic layer file (semantic.json)\n")
    
    try:
        test_query_endpoint()
    except Exception as e:
        print(f"⚠️  Query test skipped: {e}")
    
    print("\n" + "=" * 70)
    print("Testing Complete!")
    print("=" * 70)

