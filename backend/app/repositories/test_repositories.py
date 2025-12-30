"""
Test Repositories

Run this to verify both ReportRepository and SemanticRepository work correctly.

Usage:
    python -m app.repositories.test_repositories
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.repositories.semantic_repository import FileSemanticRepository
from app.repositories.report_repository import AsyncReportRepository
from app.core.models.report import Report
from app.core.models.query import QueryRequest


async def test_semantic_repository():
    """Test SemanticRepository"""
    print("=" * 60)
    print("Testing SemanticRepository")
    print("=" * 60)
    
    try:
        repo = FileSemanticRepository()
        
        # Test load_semantic
        print("\n1. Testing load_semantic()...")
        semantic = await repo.load_semantic()
        print(f"✅ Semantic layer loaded successfully!")
        print(f"   Tables found: {len(semantic.tables)}")
        
        # Test table access
        if semantic.tables:
            table_name = list(semantic.tables.keys())[0]
            table = semantic.get_table(table_name)
            print(f"\n2. Testing table access...")
            print(f"   Table: {table_name}")
            print(f"   Columns: {len(table.columns)}")
            print(f"   Dimensions: {len(table.dimensions)}")
            print(f"   Measures: {len(table.measures)}")
            print(f"✅ Table access works!")
        
        # Test reload
        print("\n3. Testing reload_semantic()...")
        semantic2 = await repo.reload_semantic()
        assert len(semantic2.tables) == len(semantic.tables)
        print(f"✅ Reload works!")
        
        print("\n✅ All SemanticRepository tests PASSED!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ SemanticRepository test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_report_repository():
    """Test ReportRepository"""
    print("=" * 60)
    print("Testing ReportRepository")
    print("=" * 60)
    
    try:
        repo = AsyncReportRepository()
        test_user_id = "test_user_123"
        
        # Test 1: Save report
        print("\n1. Testing save_report()...")
        from datetime import timezone
        test_report = Report(
            report_id=0,  # Will be set by DB
            report_name="Test Report",
            user_question="Show me test data",
            generated_sql="SELECT 1 as test",
            user_id=test_user_id,
            created_at=datetime.now(timezone.utc)
        )
        
        report_id = await repo.save_report(test_report)
        print(f"✅ Report saved with ID: {report_id}")
        
        # Test 2: Get report
        print("\n2. Testing get_report()...")
        retrieved = await repo.get_report(report_id, test_user_id)
        assert retrieved is not None
        assert retrieved.report_id == report_id
        assert retrieved.report_name == "Test Report"
        print(f"✅ Report retrieved: {retrieved.report_name}")
        
        # Test 3: List reports
        print("\n3. Testing list_reports()...")
        reports, total = await repo.list_reports(test_user_id, limit=10, offset=0)
        assert total > 0
        assert len(reports) > 0
        print(f"✅ Listed {len(reports)} reports (total: {total})")
        
        # Test 4: Update report
        print("\n4. Testing update_report()...")
        retrieved.report_name = "Updated Test Report"
        updated = await repo.update_report(report_id, test_user_id, retrieved)
        assert updated == True
        
        # Verify update
        updated_report = await repo.get_report(report_id, test_user_id)
        assert updated_report.report_name == "Updated Test Report"
        print(f"✅ Report updated successfully")
        
        # Test 5: Execute saved SQL
        print("\n5. Testing execute_saved_sql()...")
        report, rows = await repo.execute_saved_sql(report_id, test_user_id, max_rows=10)
        assert report is not None
        print(f"✅ SQL executed: {len(rows)} rows returned")
        
        # Test 6: Delete report (cleanup)
        print("\n6. Testing delete_report()...")
        deleted = await repo.delete_report(report_id, test_user_id)
        assert deleted == True
        print(f"✅ Report deleted (soft delete)")
        
        # Verify it's deleted
        deleted_report = await repo.get_report(report_id, test_user_id)
        assert deleted_report is None or deleted_report.status == "deleted"
        print(f"✅ Delete verified")
        
        print("\n✅ All ReportRepository tests PASSED!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ ReportRepository test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Repository Tests")
    print("=" * 60)
    
    results = []
    
    # Test SemanticRepository
    results.append(await test_semantic_repository())
    
    # Test ReportRepository
    results.append(await test_report_repository())
    
    # Summary
    print("=" * 60)
    if all(results):
        print("✅ ALL REPOSITORY TESTS PASSED!")
    else:
        print("❌ Some tests failed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

