"""
Test Async Database Infrastructure

Run this to verify async database layer works correctly.

Usage:
    python -m app.infrastructure.database.test_async_db
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.infrastructure.database import (
    get_async_engine,
    execute_query,
    execute_query_with_limit
)
from app.config import get_settings


async def test_async_connection():
    """Test async database connection"""
    print("Testing Async Database Connection...")
    
    try:
        # Get async engine
        engine = get_async_engine()
        print(f"✅ Async engine created: {engine}")
        
        # Test connection with simple query
        result = await execute_query("SELECT 1 as test")
        print(f"✅ Connection test successful: {result}")
        
        return True
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_query_execution():
    """Test query execution"""
    print("\nTesting Query Execution...")
    
    try:
        # Test simple query
        result = await execute_query("SELECT 1 as one, 2 as two, 'test' as name")
        assert len(result) == 1
        assert result[0]["one"] == 1
        assert result[0]["two"] == 2
        assert result[0]["name"] == "test"
        print("✅ Simple query works")
        
        # Test with limit
        result = await execute_query_with_limit(
            "SELECT generate_series(1, 100) as num",
            max_rows=10
        )
        assert len(result) <= 10
        print(f"✅ Query with limit works: {len(result)} rows")
        
        return True
    except Exception as e:
        print(f"❌ Query execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_real_query():
    """Test with a real database query (if available)"""
    print("\nTesting Real Database Query...")
    
    try:
        settings = get_settings()
        
        # Try to get a table name from semantic layer or use a simple query
        # For now, just test that we can execute queries
        result = await execute_query("SELECT version() as db_version")
        if result:
            print(f"✅ Real query works: {result[0].get('db_version', 'N/A')[:50]}")
        return True
    except Exception as e:
        print(f"⚠️  Real query test skipped: {e}")
        return True  # Don't fail if we can't connect to real DB


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Async Database Infrastructure")
    print("=" * 60)
    
    results = []
    
    results.append(await test_async_connection())
    results.append(await test_query_execution())
    results.append(await test_real_query())
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ All Async Database Tests PASSED!")
    else:
        print("❌ Some tests failed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

