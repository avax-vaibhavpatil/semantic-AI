#!/usr/bin/env python3
"""
Test queries on both tables (gwanalytics and stock_planning_data)

This script tests:
1. Semantic layer loads both tables correctly
2. Queries on gwanalytics table work
3. Queries on stock_planning_data table work
4. AI correctly identifies which table to use based on query
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.repositories.semantic_repository import MultiFileSemanticRepository
from app.services.query_service import QueryService
from app.infrastructure.ai.router import ProviderRouter
from app.infrastructure.ai.providers.claude_provider import ClaudeProvider
from app.infrastructure.ai.providers.groq_provider import GroqProvider
from app.core.models.query import QueryRequest
from app.config import get_logger

logger = get_logger(__name__)


async def test_semantic_loading():
    """Test that both semantic files are loaded"""
    print("=" * 80)
    print("TEST 1: Semantic Layer Loading")
    print("=" * 80)
    
    repo = MultiFileSemanticRepository()
    semantic = await repo.load_semantic()
    
    tables = semantic.get_all_table_names()
    print(f"\n✅ Loaded {len(tables)} tables:")
    for table_name in sorted(tables):
        table = semantic.get_table(table_name)
        col_count = len(table.columns)
        dim_count = len(table.dimensions)
        meas_count = len(table.measures)
        print(f"   • {table_name}")
        print(f"     Columns: {col_count}, Dimensions: {dim_count}, Measures: {meas_count}")
    
    # Check both tables exist
    has_gwanalytics = semantic.has_table("public.gwanalytics")
    has_stock_planning = semantic.has_table("public.stock_planning_data")
    
    print(f"\n✅ Table Check:")
    print(f"   • public.gwanalytics: {'✅' if has_gwanalytics else '❌'}")
    print(f"   • public.stock_planning_data: {'✅' if has_stock_planning else '❌'}")
    
    if not (has_gwanalytics and has_stock_planning):
        print("\n❌ ERROR: Both tables not found!")
        return None
    
    return semantic, repo


async def test_gwanalytics_queries(query_service: QueryService):
    """Test queries on gwanalytics table"""
    print("\n" + "=" * 80)
    print("TEST 2: Queries on gwanalytics Table")
    print("=" * 80)
    
    test_queries = [
        "Show me total sales by customer",
        "What are the top 5 customers by sales?",
        "Show me sales data",
    ]
    
    results = []
    for i, question in enumerate(test_queries, 1):
        print(f"\n📝 Query {i}: {question}")
        try:
            request = QueryRequest(question=question, max_rows=10)
            result = await query_service.execute_query(request)
            
            print(f"   ✅ SQL Generated: {result.query.sql[:100]}...")
            print(f"   ✅ Rows returned: {result.row_count}")
            print(f"   ✅ Execution time: {result.execution_time_ms:.2f}ms")
            
            # Check if SQL uses correct table
            sql_lower = result.query.sql.lower()
            if "gwanalytics" in sql_lower or "gws_" in sql_lower:
                print(f"   ✅ Correct table used: gwanalytics")
            else:
                print(f"   ⚠️  Warning: May not be using gwanalytics table")
            
            if result.row_count > 0:
                print(f"   📊 Sample data: {result.rows[0] if result.rows else 'N/A'}")
            
            results.append((question, True, result))
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append((question, False, str(e)))
    
    return results


async def test_stock_planning_queries(query_service: QueryService):
    """Test queries on stock_planning_data table"""
    print("\n" + "=" * 80)
    print("TEST 3: Queries on stock_planning_data Table")
    print("=" * 80)
    
    test_queries = [
        "Show me stock levels by item",
        "What items have low stock?",
        "Show me reorder levels",
        "What is the stock level for items?",
    ]
    
    results = []
    for i, question in enumerate(test_queries, 1):
        print(f"\n📝 Query {i}: {question}")
        try:
            request = QueryRequest(question=question, max_rows=10)
            result = await query_service.execute_query(request)
            
            print(f"   ✅ SQL Generated: {result.query.sql[:100]}...")
            print(f"   ✅ Rows returned: {result.row_count}")
            print(f"   ✅ Execution time: {result.execution_time_ms:.2f}ms")
            
            # Check if SQL uses correct table
            sql_lower = result.query.sql.lower()
            if "stock_planning_data" in sql_lower or "spd_" in sql_lower:
                print(f"   ✅ Correct table used: stock_planning_data")
            else:
                print(f"   ⚠️  Warning: May not be using stock_planning_data table")
            
            if result.row_count > 0:
                print(f"   📊 Sample data: {result.rows[0] if result.rows else 'N/A'}")
            
            results.append((question, True, result))
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append((question, False, str(e)))
    
    return results


async def test_table_selection(query_service: QueryService):
    """Test that AI correctly selects table based on query"""
    print("\n" + "=" * 80)
    print("TEST 4: Table Selection Accuracy")
    print("=" * 80)
    
    test_cases = [
        ("Show me customer sales", "gwanalytics", "Should use gwanalytics for sales/customer queries"),
        ("What is the stock level?", "stock_planning_data", "Should use stock_planning_data for stock queries"),
        ("Show me items with low inventory", "stock_planning_data", "Should use stock_planning_data for inventory queries"),
        ("What are the top salespeople?", "gwanalytics", "Should use gwanalytics for salesperson queries"),
    ]
    
    results = []
    for question, expected_table, description in test_cases:
        print(f"\n📝 Test: {description}")
        print(f"   Question: {question}")
        print(f"   Expected table: {expected_table}")
        
        try:
            request = QueryRequest(question=question, max_rows=5)
            result = await query_service.execute_query(request)
            
            sql_lower = result.query.sql.lower()
            if expected_table == "gwanalytics":
                uses_correct = "gwanalytics" in sql_lower or "gws_" in sql_lower
            else:
                uses_correct = "stock_planning_data" in sql_lower or "spd_" in sql_lower
            
            if uses_correct:
                print(f"   ✅ Correct table selected!")
            else:
                print(f"   ❌ Wrong table selected!")
                print(f"   SQL: {result.query.sql[:150]}")
            
            results.append((question, uses_correct))
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append((question, False))
    
    return results


async def main():
    """Run all tests"""
    print("=" * 80)
    print("BACKEND TEST: Both Tables (gwanalytics + stock_planning_data)")
    print("=" * 80)
    
    try:
        # Test 1: Semantic loading
        semantic_result = await test_semantic_loading()
        if semantic_result is None:
            print("\n❌ Semantic layer test failed. Exiting.")
            return
        
        semantic, repo = semantic_result
        
        # Initialize query service
        print("\n" + "=" * 80)
        print("Initializing Query Service...")
        print("=" * 80)
        
        claude_provider = ClaudeProvider()
        groq_provider = GroqProvider()
        providers = [p for p in [claude_provider, groq_provider] if p.is_configured()]
        
        if not providers:
            print("❌ No AI providers configured. Set ANTHROPIC_API_KEY or GROQ_API_KEY")
            return
        
        ai_router = ProviderRouter(providers)
        query_service = QueryService(
            semantic_repository=repo,
            ai_router=ai_router,
        )
        print("✅ QueryService initialized")
        
        # Test 2: gwanalytics queries
        gwanalytics_results = await test_gwanalytics_queries(query_service)
        
        # Test 3: stock_planning queries
        stock_results = await test_stock_planning_queries(query_service)
        
        # Test 4: Table selection
        selection_results = await test_table_selection(query_service)
        
        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        gwanalytics_success = sum(1 for _, success, _ in gwanalytics_results if success)
        stock_success = sum(1 for _, success, _ in stock_results if success)
        selection_success = sum(1 for _, success in selection_results if success)
        
        print(f"\n✅ gwanalytics queries: {gwanalytics_success}/{len(gwanalytics_results)} passed")
        print(f"✅ stock_planning queries: {stock_success}/{len(stock_results)} passed")
        print(f"✅ Table selection: {selection_success}/{len(selection_results)} passed")
        
        total_tests = len(gwanalytics_results) + len(stock_results) + len(selection_results)
        total_success = gwanalytics_success + stock_success + selection_success
        
        print(f"\n📊 Overall: {total_success}/{total_tests} tests passed")
        
        if total_success == total_tests:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {total_tests - total_success} test(s) failed")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())




