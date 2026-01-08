#!/usr/bin/env python3
"""
Test script to verify LLM can query stock_gw table
"""
import asyncio
import json
from app.repositories.semantic_repository import MultiFileSemanticRepository
from app.services.query_service import QueryService
from app.infrastructure.ai.router import ProviderRouter
from app.infrastructure.ai.providers.claude_provider import ClaudeProvider
from app.infrastructure.ai.providers.groq_provider import GroqProvider
from app.core.models.query import QueryRequest


async def test_stock_gw_query():
    """
    Test that LLM can generate and execute queries on stock_gw table
    """
    print("=" * 80)
    print("TESTING STOCK_GW TABLE QUERIES")
    print("=" * 80)
    print()
    
    # Initialize services
    print("1. Initializing services...")
    semantic_repo = MultiFileSemanticRepository()
    print(f"   ✅ Semantic repository initialized")
    
    # Load semantic layer to verify stock_gw is loaded
    print("\n2. Loading semantic layer...")
    semantic_layer = await semantic_repo.load_semantic()
    print(f"   ✅ Loaded {len(semantic_layer.tables)} table(s)")
    
    # Check if stock_gw table is in semantic layer
    stock_gw_key = "public.stock_gw"
    if stock_gw_key in semantic_layer.tables:
        table = semantic_layer.tables[stock_gw_key]
        print(f"   ✅ Found table: {stock_gw_key}")
        print(f"      - Columns: {len(table.columns)}")
        print(f"      - Dimensions: {len(table.dimensions)}")
        print(f"      - Measures: {len(table.measures)}")
    else:
        print(f"   ❌ Table '{stock_gw_key}' not found in semantic layer")
        print(f"   Available tables: {list(semantic_layer.tables.keys())}")
        return
    
    # Initialize AI providers
    print("\n3. Initializing AI providers...")
    claude_provider = ClaudeProvider()
    groq_provider = GroqProvider()
    providers = [claude_provider, groq_provider]
    ai_router = ProviderRouter(providers)
    print(f"   ✅ AI router initialized")
    print(f"      - Claude configured: {claude_provider.is_configured()}")
    print(f"      - Groq configured: {groq_provider.is_configured()}")
    
    # Create query service
    print("\n4. Creating query service...")
    query_service = QueryService(
        semantic_repository=semantic_repo,
        ai_router=ai_router,
    )
    print(f"   ✅ Query service created")
    
    # Test queries
    test_queries = [
        "What is the total stock value by branch?",
        "Show me the top 5 items by stock quantity",
        "What is the total stock value aged above 4 years?",
    ]
    
    print("\n" + "=" * 80)
    print("TESTING QUERIES")
    print("=" * 80)
    print()
    
    for i, question in enumerate(test_queries, 1):
        print(f"Query {i}: {question}")
        print("-" * 80)
        
        try:
            request = QueryRequest(question=question, max_rows=10)
            result = await query_service.execute_query(request)
            
            print(f"✅ Success!")
            print(f"   SQL: {result.query.sql}")
            print(f"   Rows returned: {result.row_count}")
            print(f"   Execution time: {result.execution_time_ms:.2f}ms")
            
            if result.rows:
                print(f"\n   Sample data (first {min(3, len(result.rows))} rows):")
                for j, row in enumerate(result.rows[:3], 1):
                    print(f"   Row {j}: {json.dumps(row, default=str)}")
            
            if result.warning:
                print(f"   ⚠️  Warning: {result.warning}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(test_stock_gw_query())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

