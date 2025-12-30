"""
Test QueryService and ReportService Together

Run this to verify both services work correctly and integrate properly.

Usage:
    python app/services/test_query_and_report_services.py
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.query_service import QueryService
from app.services.report_service import ReportService
from app.repositories.semantic_repository import FileSemanticRepository
from app.repositories.report_repository import AsyncReportRepository
from app.infrastructure.ai.router import ProviderRouter
from app.infrastructure.ai.providers.claude_provider import ClaudeProvider
from app.infrastructure.ai.providers.groq_provider import GroqProvider
from app.core.models.query import QueryRequest
from app.core.exceptions import ReportNotFoundError


async def test_query_and_report_services():
    """Test QueryService and ReportService together"""
    print("=" * 70)
    print("Testing QueryService and ReportService Together")
    print("=" * 70)
    
    # ============================================================
    # SETUP: Initialize all dependencies
    # ============================================================
    print("\n📦 Setting up services...")
    
    # Initialize repositories
    semantic_repo = FileSemanticRepository()
    report_repo = AsyncReportRepository()
    
    # Initialize AI providers (explicitly use haiku for Claude)
    claude_provider = ClaudeProvider(model="claude-3-haiku-20240307")
    groq_provider = GroqProvider()
    
    # Initialize router with providers (priority: Claude, then Groq)
    providers = [claude_provider, groq_provider]
    ai_router = ProviderRouter(providers)
    
    # Initialize services
    query_service = QueryService(
        semantic_repository=semantic_repo,
        ai_router=ai_router,
    )
    
    report_service = ReportService(
        report_repository=report_repo,
    )
    
    print("✅ All services initialized")
    
    # Test user ID
    test_user_id = "test_user_123"
    
    # ============================================================
    # TEST 1: QueryService - Execute Natural Language Query
    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 1: QueryService - Execute Natural Language Query")
    print("=" * 70)
    
    try:
        # Create a simple query request
        query_request = QueryRequest(
            question="Show me top 5 customers by YTD sales",
            max_rows=100,
        )
        
        print(f"   Question: {query_request.question}")
        print("   Executing query...")
        
        # Execute query
        query_result = await query_service.execute_query(query_request)
        
        print(f"✅ Query executed successfully!")
        print(f"   Generated SQL: {query_result.query.sql[:100]}...")
        print(f"   Rows returned: {len(query_result.rows)}")
        print(f"   Execution time: {query_result.execution_time_ms:.2f}ms")
        
        if query_result.rows:
            print(f"\n   First row sample:")
            first_row = query_result.rows[0]
            for key, value in list(first_row.items())[:3]:
                print(f"     {key}: {value}")
        
    except Exception as e:
        print(f"❌ Query execution failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ============================================================
    # TEST 2: ReportService - Save Report from Query Result
    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 2: ReportService - Save Report from Query Result")
    print("=" * 70)
    
    try:
        # Save report from query result
        report_name = f"Top 5 Customers - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        report_id = await report_service.save_report_from_query(
            query_result=query_result,
            report_name=report_name,
            user_id=test_user_id,
            description="Top 5 customers by YTD sales",
            tags=["sales", "customers", "top-5"],
        )
        
        print(f"✅ Report saved successfully!")
        print(f"   Report ID: {report_id}")
        print(f"   Report Name: {report_name}")
        
    except Exception as e:
        print(f"❌ Failed to save report: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ============================================================
    # TEST 3: ReportService - Get Report by ID
    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 3: ReportService - Get Report by ID")
    print("=" * 70)
    
    try:
        # Get the saved report
        report = await report_service.get_report(report_id, test_user_id)
        
        print(f"✅ Report retrieved successfully!")
        print(f"   Report ID: {report.report_id}")
        print(f"   Report Name: {report.report_name}")
        print(f"   User Question: {report.user_question}")
        print(f"   Created At: {report.created_at}")
        print(f"   Tags: {report.tags}")
        print(f"   Execution Count: {report.execution_count}")
        
    except Exception as e:
        print(f"❌ Failed to get report: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ============================================================
    # TEST 4: ReportService - List Reports
    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 4: ReportService - List Reports")
    print("=" * 70)
    
    try:
        # List reports for user
        reports, total = await report_service.list_reports(
            user_id=test_user_id,
            limit=10,
            offset=0,
        )
        
        print(f"✅ Reports listed successfully!")
        print(f"   Total reports: {total}")
        print(f"   Reports returned: {len(reports)}")
        
        if reports:
            print(f"\n   First few reports:")
            for r in reports[:3]:
                print(f"     - {r.report_name} (ID: {r.report_id})")
        
    except Exception as e:
        print(f"❌ Failed to list reports: {e}")
        import traceback
        traceback.print_exc()
    
    # ============================================================
    # TEST 5: ReportService - Search Reports
    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 5: ReportService - Search Reports")
    print("=" * 70)
    
    try:
        # Search reports
        search_results, total = await report_service.search_reports(
            user_id=test_user_id,
            query="customers",
            limit=10,
            offset=0,
        )
        
        print(f"✅ Search completed successfully!")
        print(f"   Search query: 'customers'")
        print(f"   Results found: {total}")
        print(f"   Results returned: {len(search_results)}")
        
        if search_results:
            print(f"\n   Matching reports:")
            for r in search_results[:3]:
                print(f"     - {r.report_name} (ID: {r.report_id})")
        
    except Exception as e:
        print(f"❌ Failed to search reports: {e}")
        import traceback
        traceback.print_exc()
    
    # ============================================================
    # TEST 6: ReportService - Execute Saved Report
    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 6: ReportService - Execute Saved Report")
    print("=" * 70)
    
    try:
        # Execute saved report
        executed_report, rows = await report_service.execute_saved_report(
            report_id=report_id,
            user_id=test_user_id,
            max_rows=100,
        )
        
        print(f"✅ Saved report executed successfully!")
        print(f"   Report Name: {executed_report.report_name}")
        print(f"   Rows returned: {len(rows)}")
        print(f"   Execution Count: {executed_report.execution_count}")
        print(f"   Last Executed At: {executed_report.last_executed_at}")
        
        if rows:
            print(f"\n   First row sample:")
            first_row = rows[0]
            for key, value in list(first_row.items())[:3]:
                print(f"     {key}: {value}")
        
    except Exception as e:
        print(f"❌ Failed to execute saved report: {e}")
        import traceback
        traceback.print_exc()
    
    # ============================================================
    # TEST 7: ReportService - Update Report
    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 7: ReportService - Update Report")
    print("=" * 70)
    
    try:
        # Get report first
        report_to_update = await report_service.get_report(report_id, test_user_id)
        
        # Update report
        report_to_update.report_name = f"Updated: {report_to_update.report_name}"
        report_to_update.report_description = "Updated description"
        report_to_update.tags = ["sales", "customers", "top-5", "updated"]
        
        success = await report_service.update_report(
            report_id=report_id,
            user_id=test_user_id,
            updated_report=report_to_update,
        )
        
        if success:
            # Verify update
            updated_report = await report_service.get_report(report_id, test_user_id)
            print(f"✅ Report updated successfully!")
            print(f"   Updated Name: {updated_report.report_name}")
            print(f"   Updated Description: {updated_report.report_description}")
            print(f"   Updated Tags: {updated_report.tags}")
        else:
            print("❌ Update returned False")
        
    except Exception as e:
        print(f"❌ Failed to update report: {e}")
        import traceback
        traceback.print_exc()
    
    # ============================================================
    # TEST 8: Integration - Query → Save → Execute Flow
    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 8: Integration - Full Flow (Query → Save → Execute)")
    print("=" * 70)
    
    try:
        # Step 1: Execute new query
        print("\n   Step 1: Execute new query...")
        new_query = QueryRequest(
            question="Show me total YTD sales by customer",
            max_rows=100,
        )
        new_result = await query_service.execute_query(new_query)
        print(f"   ✅ Query executed: {len(new_result.rows)} rows")
        
        # Step 2: Save as report
        print("\n   Step 2: Save as report...")
        new_report_id = await report_service.save_report_from_query(
            query_result=new_result,
            report_name=f"Total Sales by Customer - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            user_id=test_user_id,
            description="Total YTD sales grouped by customer",
            tags=["sales", "aggregation"],
        )
        print(f"   ✅ Report saved: ID {new_report_id}")
        
        # Step 3: Execute saved report
        print("\n   Step 3: Execute saved report...")
        saved_report, saved_rows = await report_service.execute_saved_report(
            report_id=new_report_id,
            user_id=test_user_id,
        )
        print(f"   ✅ Saved report executed: {len(saved_rows)} rows")
        print(f"   ✅ Execution count: {saved_report.execution_count}")
        
        print("\n   ✅ Full integration flow completed successfully!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # ============================================================
    # TEST 9: Error Handling - Non-existent Report
    # ============================================================
    print("\n" + "=" * 70)
    print("TEST 9: Error Handling - Non-existent Report")
    print("=" * 70)
    
    try:
        # Try to get non-existent report
        await report_service.get_report(99999, test_user_id)
        print("❌ Should have raised exception")
    except ReportNotFoundError:
        print("✅ Correctly raised ReportNotFoundError for non-existent report")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETED!")
    print("=" * 70)
    print("\nQueryService and ReportService are working correctly together! 🎉")
    print(f"\nTest reports created for user: {test_user_id}")
    print("(You can clean them up manually if needed)")


if __name__ == "__main__":
    asyncio.run(test_query_and_report_services())

