#!/usr/bin/env python3
"""
Demo: How logging works in your project

Run this to see logging in action:
    python -m app.config.demo_logging
"""
import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import setup_logging, get_logger

# Setup logging
setup_logging()

# Get logger
logger = get_logger(__name__)


def process_query(question: str, user_id: str):
    """Simulate query processing - like your /ask endpoint"""
    logger.info(
        "Processing query request",
        extra={
            "question": question[:50],
            "user_id": user_id
        }
    )
    
    # Simulate AI call
    logger.debug("Calling AI model", extra={"provider": "groq", "model": "llama-3.1-8b-instant"})
    time.sleep(0.1)  # Simulate API call
    sql = "SELECT branch_name, SUM(sales) as total_sales FROM sales GROUP BY branch_name LIMIT 10"
    
    logger.info(
        "AI model call successful",
        extra={
            "duration_seconds": 0.1,
            "sql_length": len(sql),
            "tokens_used": 150
        }
    )
    
    # Simulate SQL execution
    logger.debug("Executing SQL", extra={"sql": sql[:100]})
    results = [{"branch_name": f"Branch {i}", "total_sales": 1000 * i} for i in range(10)]
    
    logger.info(
        "Query executed successfully",
        extra={
            "rows_returned": len(results),
            "total_duration": 0.2
        }
    )
    
    return results


def save_report(user_id: str, report_name: str):
    """Simulate report saving - like your /reports endpoint"""
    logger.info(
        "Saving report",
        extra={
            "user_id": user_id,
            "report_name": report_name
        }
    )
    
    report_id = 123
    
    logger.info(
        "Report saved successfully",
        extra={
            "user_id": user_id,
            "report_id": report_id,
            "report_name": report_name
        }
    )
    
    return report_id


def simulate_error():
    """Simulate an error scenario"""
    try:
        logger.info("Attempting database operation")
        raise ValueError("Database connection failed")
    except Exception as e:
        logger.error(
            "Database operation failed",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )


if __name__ == "__main__":
    print("=" * 70)
    print("LOGGING DEMO - What you'll see in your project")
    print("=" * 70)
    print()
    
    print("📝 Example 1: User asks a question")
    print("-" * 70)
    process_query("Show me top 10 branches by sales", "user123")
    print()
    
    print("📝 Example 2: User saves a report")
    print("-" * 70)
    save_report("user123", "Monthly Sales Report")
    print()
    
    print("📝 Example 3: Error occurs")
    print("-" * 70)
    simulate_error()
    print()
    
    print("=" * 70)
    print("✅ Notice how logs include:")
    print("  - Timestamp (when it happened)")
    print("  - Log level (INFO, ERROR, etc.)")
    print("  - Logger name (which module)")
    print("  - Message (what happened)")
    print("  - Extra context (user_id, question, etc.)")
    print()
    print("💡 In production, these are JSON format (easy to search)")
    print("💡 In development, they're human-readable")
    print("=" * 70)

