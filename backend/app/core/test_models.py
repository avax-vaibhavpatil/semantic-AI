"""
Test Core Domain Models

Quick test to verify domain models work correctly.
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.models import Query, QueryRequest, QueryResult, Report, SemanticLayer
from app.core.exceptions import QueryValidationError
from app.core import constants


def test_query_models():
    """Test Query domain models"""
    print("Testing Query Models...")
    
    # Test QueryRequest
    request = QueryRequest(
        question="Show me top 10 customers",
        max_rows=10
    )
    assert request.question == "Show me top 10 customers"
    assert request.max_rows == 10
    print("✅ QueryRequest works")
    
    # Test Query
    query = Query(
        question="Show me top 10 customers",
        sql="SELECT * FROM customers LIMIT 10",
        generated_at=datetime.utcnow()
    )
    assert query.question == "Show me top 10 customers"
    assert "SELECT" in query.sql
    print("✅ Query works")
    
    # Test QueryResult
    result = QueryResult(
        query=query,
        rows=[{"id": 1, "name": "Customer 1"}],
        row_count=1,
        execution_time_ms=50.5,
        executed_at=datetime.utcnow()
    )
    assert result.row_count == 1
    assert not result.is_empty
    print("✅ QueryResult works")
    
    print("✅ All Query models work!\n")


def test_report_model():
    """Test Report domain model"""
    print("Testing Report Model...")
    
    report = Report(
        report_id=1,
        report_name="Top Customers",
        user_question="Show top customers",
        generated_sql="SELECT * FROM customers",
        user_id="user123",
        created_at=datetime.utcnow()
    )
    
    assert report.report_id == 1
    assert report.is_active()
    assert report.execution_count == 0
    
    # Test mark_executed
    report.mark_executed()
    assert report.execution_count == 1
    assert report.last_executed_at is not None
    
    # Test toggle_favorite
    report.toggle_favorite()
    assert report.is_favorite == True
    
    print("✅ Report model works!\n")


def test_semantic_layer():
    """Test SemanticLayer model"""
    print("Testing SemanticLayer Model...")
    
    # Create from dict (like loading from JSON)
    semantic_data = {
        "tables": {
            "customers": {
                "description": "Customer table",
                "columns": {
                    "customer_id": {"type": "dimension"},
                    "customer_name": {"type": "dimension"},
                    "sales": {"type": "measure"}
                },
                "dimensions": ["customer_id", "customer_name"],
                "measures": ["sales"],
                "time_columns": [],
                "derived_measures": []
            }
        }
    }
    
    semantic = SemanticLayer.from_dict(semantic_data)
    
    assert semantic.has_table("customers")
    assert not semantic.has_table("nonexistent")
    
    table = semantic.get_table("customers")
    assert table is not None
    assert table.has_column("customer_id")
    assert table.is_dimension("customer_id")
    assert table.is_measure("sales")
    
    print("✅ SemanticLayer model works!\n")


def test_constants():
    """Test constants"""
    print("Testing Constants...")
    
    assert constants.MAX_QUERY_ROWS == 10000
    assert constants.DEFAULT_MAX_ROWS == 500
    assert constants.REPORT_STATUS_ACTIVE == "active"
    
    print("✅ Constants work!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Core Domain Models")
    print("=" * 60)
    print()
    
    try:
        test_query_models()
        test_report_model()
        test_semantic_layer()
        test_constants()
        
        print("=" * 60)
        print("✅ All Core Domain Models Tests PASSED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

