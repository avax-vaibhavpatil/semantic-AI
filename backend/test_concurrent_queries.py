"""
Test Concurrent Queries from Multiple Users

This test simulates multiple users making queries simultaneously
to verify the API handles concurrency correctly.
"""

import asyncio
import aiohttp
import time
from typing import List, Dict, Any

BASE_URL = "http://localhost:8000"

# Different queries from different "users"
USER_QUERIES = [
    {"user_id": "user1", "question": "Show me top 5 customers by YTD sales", "max_rows": 5},
    {"user_id": "user2", "question": "Show me total YTD sales by customer", "max_rows": 10},
    {"user_id": "user3", "question": "Show me customers with highest profit", "max_rows": 5},
    {"user_id": "user4", "question": "Show me top 3 customers by budget", "max_rows": 3},
    {"user_id": "user5", "question": "Show me customers with sales greater than 1000000", "max_rows": 10},
]


async def execute_query(session: aiohttp.ClientSession, user_query: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single query for a user"""
    user_id = user_query["user_id"]
    question = user_query["question"]
    
    start_time = time.time()
    try:
        async with session.post(
            f"{BASE_URL}/api/v1/query",
            json={
                "question": question,
                "max_rows": user_query["max_rows"]
            },
            timeout=aiohttp.ClientTimeout(total=60)
        ) as response:
            result = await response.json()
            elapsed = (time.time() - start_time) * 1000
            
            return {
                "user_id": user_id,
                "question": question,
                "status": response.status,
                "success": result.get("success", False),
                "row_count": result.get("row_count", 0),
                "execution_time_ms": result.get("execution_time_ms", 0),
                "total_time_ms": elapsed,
                "error": result.get("error") if response.status != 200 else None,
            }
    except asyncio.TimeoutError:
        return {
            "user_id": user_id,
            "question": question,
            "status": "timeout",
            "success": False,
            "error": "Request timed out",
            "total_time_ms": (time.time() - start_time) * 1000,
        }
    except Exception as e:
        return {
            "user_id": user_id,
            "question": question,
            "status": "error",
            "success": False,
            "error": str(e),
            "total_time_ms": (time.time() - start_time) * 1000,
        }


async def test_concurrent_queries():
    """Test multiple users making queries simultaneously"""
    print("=" * 70)
    print("Testing Concurrent Queries from Multiple Users")
    print("=" * 70)
    print(f"\nSimulating {len(USER_QUERIES)} users making queries simultaneously...")
    print()
    
    async with aiohttp.ClientSession() as session:
        # Execute all queries concurrently
        start_time = time.time()
        tasks = [execute_query(session, query) for query in USER_QUERIES]
        results = await asyncio.gather(*tasks)
        total_time = (time.time() - start_time) * 1000
    
    # Display results
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()
    
    successful = 0
    failed = 0
    
    for i, result in enumerate(results, 1):
        status_icon = "✅" if result["success"] else "❌"
        print(f"{status_icon} User {result['user_id']}:")
        print(f"   Question: {result['question'][:50]}...")
        print(f"   Status: {result['status']}")
        
        if result["success"]:
            successful += 1
            print(f"   Rows: {result['row_count']}")
            print(f"   Execution time: {result['execution_time_ms']:.2f}ms")
            print(f"   Total time: {result['total_time_ms']:.2f}ms")
        else:
            failed += 1
            print(f"   Error: {result.get('error', 'Unknown error')[:100]}")
        
        print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total queries: {len(USER_QUERIES)}")
    print(f"Successful: {successful} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Total time (all queries): {total_time:.2f}ms")
    print(f"Average time per query: {total_time / len(USER_QUERIES):.2f}ms")
    print()
    
    if successful == len(USER_QUERIES):
        print("🎉 All concurrent queries succeeded!")
        print("✅ API handles concurrency correctly")
    elif successful > 0:
        print(f"⚠️  {successful}/{len(USER_QUERIES)} queries succeeded")
        print("   Some queries may have failed due to:")
        print("   - Database connection limits")
        print("   - AI provider rate limits")
        print("   - Query complexity")
    else:
        print("❌ All queries failed")
        print("   Check server logs for details")


if __name__ == "__main__":
    print("\n⚠️  Make sure the server is running:")
    print("   uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000\n")
    time.sleep(2)
    
    try:
        asyncio.run(test_concurrent_queries())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

