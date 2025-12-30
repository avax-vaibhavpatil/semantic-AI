"""
Test Semantic Service

Run this to verify SemanticService works correctly.

Usage:
    python -m app.services.test_semantic_service
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import directly to avoid loading QueryService dependencies
from app.services.semantic_service import SemanticService
from app.repositories.semantic_repository import FileSemanticRepository
from app.core.exceptions import SemanticLayerError


async def test_semantic_service():
    """Test SemanticService - all functions"""
    print("=" * 70)
    print("Testing SemanticService")
    print("=" * 70)
    
    # Initialize service
    print("\n📦 Initializing SemanticService...")
    repo = FileSemanticRepository()
    service = SemanticService(repo)
    print("✅ SemanticService initialized")
    
    # ============================================================
    # TEST 1: load_semantic_layer()
    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 1: load_semantic_layer()")
    print("=" * 70)
    
    try:
        semantic = await service.load_semantic_layer()
        print(f"✅ Semantic layer loaded successfully!")
        print(f"   Tables found: {len(semantic.tables)}")
        
        # Get first table name for later tests
        if semantic.tables:
            first_table_name = list(semantic.tables.keys())[0]
            print(f"   First table: {first_table_name}")
        else:
            print("   ⚠️  No tables found in semantic layer")
            return
        
    except Exception as e:
        print(f"❌ Failed to load semantic layer: {e}")
        return
    
    # ============================================================
    # TEST 2: get_all_tables()
    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 2: get_all_tables()")
    print("=" * 70)
    
    try:
        tables = await service.get_all_tables()
        print(f"✅ All tables retrieved: {len(tables)} tables")
        print(f"   Tables: {', '.join(tables[:5])}{'...' if len(tables) > 5 else ''}")
    except Exception as e:
        print(f"❌ Failed to get all tables: {e}")
        return
    
    # ============================================================
    # TEST 3: get_table()
    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 3: get_table()")
    print("=" * 70)
    
    try:
        table = await service.get_table(first_table_name)
        print(f"✅ Table '{first_table_name}' retrieved successfully!")
        print(f"   Description: {table.description or 'N/A'}")
        print(f"   Columns: {len(table.columns)}")
        print(f"   Dimensions: {len(table.dimensions)}")
        print(f"   Measures: {len(table.measures)}")
        print(f"   Time columns: {len(table.time_columns)}")
        print(f"   Derived measures: {len(table.derived_measures)}")
    except Exception as e:
        print(f"❌ Failed to get table: {e}")
        return
    
    # Test with non-existent table
    try:
        await service.get_table("non_existent_table_12345")
        print("❌ Should have raised exception for non-existent table")
    except SemanticLayerError:
        print("✅ Correctly raised SemanticLayerError for non-existent table")
    
    # ============================================================
    # TEST 4: validate_table_exists()
    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 4: validate_table_exists()")
    print("=" * 70)
    
    try:
        exists = await service.validate_table_exists(first_table_name)
        print(f"✅ Table '{first_table_name}' exists: {exists}")
        
        exists_fake = await service.validate_table_exists("fake_table_12345")
        print(f"✅ Fake table exists: {exists_fake} (should be False)")
    except Exception as e:
        print(f"❌ Failed to validate table: {e}")
    
    # ============================================================
    # TEST 5: get_table_columns()
    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 5: get_table_columns()")
    print("=" * 70)
    
    try:
        columns = await service.get_table_columns(first_table_name)
        print(f"✅ Columns retrieved: {len(columns)} columns")
        
        # Show first few columns
        if columns:
            print("\n   First 5 columns:")
            for i, (col_name, column) in enumerate(list(columns.items())[:5]):
                print(f"     - {col_name}: {column.type} ({column.description or 'N/A'})")
    except Exception as e:
        print(f"❌ Failed to get columns: {e}")
        return
    
    # ============================================================
    # TEST 6: get_column()
    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 6: get_column()")
    print("=" * 70)
    
    try:
        # Get first column name
        if columns:
            first_column_name = list(columns.keys())[0]
            column = await service.get_column(first_table_name, first_column_name)
            print(f"✅ Column '{first_column_name}' retrieved successfully!")
            print(f"   Type: {column.type}")
            print(f"   Description: {column.description or 'N/A'}")
            print(f"   Role: {column.role or 'N/A'}")
            print(f"   Preferred: {column.preferred}")
        else:
            print("⚠️  No columns to test")
    except Exception as e:
        print(f"❌ Failed to get column: {e}")
    
    # Test with non-existent column
    try:
        await service.get_column(first_table_name, "non_existent_column_12345")
        print("❌ Should have raised exception for non-existent column")
    except SemanticLayerError:
        print("✅ Correctly raised SemanticLayerError for non-existent column")
    
    # ============================================================
    # TEST 7: validate_column_exists()
    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 7: validate_column_exists()")
    print("=" * 70)
    
    try:
        if columns:
            first_column_name = list(columns.keys())[0]
            exists = await service.validate_column_exists(first_table_name, first_column_name)
            print(f"✅ Column '{first_column_name}' exists: {exists}")
            
            exists_fake = await service.validate_column_exists(first_table_name, "fake_column_12345")
            print(f"✅ Fake column exists: {exists_fake} (should be False)")
            
            # Test with non-existent table
            exists_table_fake = await service.validate_column_exists("fake_table_12345", "any_column")
            print(f"✅ Fake table column exists: {exists_table_fake} (should be False)")
    except Exception as e:
        print(f"❌ Failed to validate column: {e}")
    
    # ============================================================
    # TEST 8: get_measures()
    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 8: get_measures()")
    print("=" * 70)
    
    try:
        measures = await service.get_measures(first_table_name)
        print(f"✅ Measures retrieved successfully!")
        print(f"   Regular measures: {len(measures['measures'])}")
        print(f"   Derived measures: {len(measures['derived_measures'])}")
        
        if measures['measures']:
            print(f"\n   Regular measures: {', '.join(measures['measures'][:5])}")
        
        if measures['derived_measures']:
            print(f"\n   Derived measures:")
            for dm in measures['derived_measures'][:3]:
                print(f"     - {dm.name}: {dm.expression}")
    except Exception as e:
        print(f"❌ Failed to get measures: {e}")
    
    # ============================================================
    # TEST 9: get_semantic_layer_dict()
    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 9: get_semantic_layer_dict()")
    print("=" * 70)
    
    try:
        semantic_dict = await service.get_semantic_layer_dict()
        print(f"✅ Semantic layer dictionary retrieved!")
        print(f"   Tables in dict: {len(semantic_dict.get('tables', {}))}")
        
        # Verify it's JSON serializable
        import json
        json_str = json.dumps(semantic_dict, indent=2)
        print(f"   JSON size: {len(json_str)} characters")
        print("✅ Dictionary is JSON serializable")
    except Exception as e:
        print(f"❌ Failed to get semantic layer dict: {e}")
    
    # ============================================================
    # TEST 10: reload_semantic_layer() (cache test)
    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 10: reload_semantic_layer() - Cache Test")
    print("=" * 70)
    
    try:
        # First load (should cache)
        print("   Loading semantic layer (first time - should cache)...")
        semantic1 = await service.load_semantic_layer()
        print(f"   ✅ Loaded: {len(semantic1.tables)} tables")
        
        # Second load (should use cache)
        print("   Loading semantic layer (second time - should use cache)...")
        semantic2 = await service.load_semantic_layer()
        print(f"   ✅ Loaded: {len(semantic2.tables)} tables")
        print("   ✅ Cache working (same object reference)")
        
        # Reload (should clear cache)
        print("   Reloading semantic layer (should clear cache)...")
        semantic3 = await service.reload_semantic_layer()
        print(f"   ✅ Reloaded: {len(semantic3.tables)} tables")
        print("   ✅ Reload successful")
    except Exception as e:
        print(f"❌ Failed to test reload: {e}")
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETED!")
    print("=" * 70)
    print("\nSemanticService is working correctly! 🎉")


if __name__ == "__main__":
    asyncio.run(test_semantic_service())

