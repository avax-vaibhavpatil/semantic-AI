#!/usr/bin/env python3
"""
Script to verify semantic metadata matches actual database schema
"""
import asyncio
import json
from pathlib import Path
from sqlalchemy import text
from app.infrastructure.database.connection import get_async_engine


async def get_table_columns(schema: str, table: str) -> dict:
    """
    Query database to get actual column information
    """
    engine = get_async_engine()
    
    query = text("""
        SELECT 
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = :schema 
          AND table_name = :table
        ORDER BY ordinal_position;
    """)
    
    columns = {}
    async with engine.connect() as conn:
        result = await conn.execute(query, {"schema": schema, "table": table})
        rows = result.fetchall()
        
        for row in rows:
            columns[row.column_name] = {
                "data_type": row.data_type,
                "is_nullable": row.is_nullable
            }
    
    return columns


async def verify_schema():
    """
    Verify semantic metadata matches actual database schema
    """
    # Load semantic metadata
    semantic_file = Path(__file__).parent / "metadata" / "stock_gw_semantic.json"
    
    with open(semantic_file, 'r') as f:
        semantic_data = json.load(f)
    
    # Extract table info from semantic file
    tables = semantic_data.get("tables", {})
    
    print("=" * 80)
    print("SCHEMA VERIFICATION REPORT")
    print("=" * 80)
    print()
    
    # Get the first (and likely only) table from semantic file
    if not tables:
        print("❌ No tables found in semantic file")
        return
    
    semantic_table_key = list(tables.keys())[0]
    table_info = tables[semantic_table_key]
    
    # Extract schema and table name from semantic key
    if "." in semantic_table_key:
        semantic_schema, semantic_table = semantic_table_key.split(".", 1)
    else:
        semantic_schema = "public"
        semantic_table = semantic_table_key
    
    # Check actual table name in database
    actual_table = "stock_gw"  # Found in database
    
    print(f"📊 Semantic File References: {semantic_table_key}")
    print(f"📊 Actual Database Table: public.{actual_table}")
    print()
    semantic_columns = table_info.get("columns", {})
    
    # Get actual database columns
    try:
        db_columns = await get_table_columns("public", actual_table)
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        return
    
    if not db_columns:
        print(f"❌ No columns found in database table 'public.{actual_table}'")
        return
    
    # Compare
    db_col_names = set(db_columns.keys())
    semantic_col_names = set(semantic_columns.keys())
    
    # Find differences
    missing_in_semantic = db_col_names - semantic_col_names
    extra_in_semantic = semantic_col_names - db_col_names
    common_columns = db_col_names & semantic_col_names
    
    print(f"   Database columns: {len(db_col_names)}")
    print(f"   Semantic columns: {len(semantic_col_names)}")
    print(f"   Common columns: {len(common_columns)}")
    print()
    
    # Report missing columns in semantic
    if missing_in_semantic:
        print(f"   ⚠️  MISSING in semantic file ({len(missing_in_semantic)}):")
        for col in sorted(missing_in_semantic):
            db_type = db_columns[col]["data_type"]
            print(f"      - {col} ({db_type})")
        print()
    
    # Report extra columns in semantic
    if extra_in_semantic:
        print(f"   ⚠️  EXTRA in semantic file ({len(extra_in_semantic)}):")
        for col in sorted(extra_in_semantic):
            print(f"      - {col}")
        print()
    
    # Report match status
    if not missing_in_semantic and not extra_in_semantic:
        print(f"   ✅ PERFECT MATCH! All {len(common_columns)} columns match.")
    else:
        print(f"   ⚠️  MISMATCH DETECTED")
        print(f"      Missing in semantic: {len(missing_in_semantic)}")
        print(f"      Extra in semantic: {len(extra_in_semantic)}")
    
    print()
    print("-" * 80)
    print()
    
    # Show summary
    print("📋 SUMMARY:")
    print(f"   ✅ Table name issue: Semantic file uses 'stock_gateway_data' but database has 'stock_gw'")
    print(f"   ✅ Column match: {len(common_columns)}/{len(db_col_names)} columns match")
    
    if missing_in_semantic or extra_in_semantic:
        print()
        print("⚠️  RECOMMENDATION:")
        print("   1. Update table name in semantic file from 'stock_gateway_data' to 'stock_gw'")
        if missing_in_semantic:
            print(f"   2. Add {len(missing_in_semantic)} missing column(s) to semantic file")
        if extra_in_semantic:
            print(f"   3. Remove or verify {len(extra_in_semantic)} extra column(s) in semantic file")
    
    print()
    print("📋 All database columns:")
    for col in sorted(db_col_names):
        db_type = db_columns[col]["data_type"]
        status = "✅" if col in semantic_col_names else "❌"
        print(f"   {status} {col} ({db_type})")


if __name__ == "__main__":
    try:
        asyncio.run(verify_schema())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

