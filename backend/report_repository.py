"""
Report Repository - Database Access Layer

Purpose: Centralize all database operations for saved reports
- Keeps SQL queries in one place
- Prevents SQL injection through parameterized queries
- Handles connections and errors properly
- Makes code testable and maintainable

Design Pattern: Repository Pattern
- Separates data access from business logic
- Makes it easy to switch databases later (PostgreSQL → MySQL, etc.)
- Each method does ONE thing (Single Responsibility Principle)
"""

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from typing import List, Dict, Optional, Any
import logging
import time
from db_connector import get_engine
from models import (
    SaveReportRequest, 
    UpdateReportRequest,
    database_row_to_report_response
)

# Set up logging for debugging
logger = logging.getLogger(__name__)

# ==============================================================================
# REPOSITORY CLASS
# ==============================================================================

class ReportRepository:
    """
    Repository for saved reports
    
    Responsibilities:
    - Execute SQL queries safely (parameterized queries)
    - Handle database connections
    - Convert database rows to Python objects
    - Handle errors gracefully
    
    Does NOT:
    - Contain business logic (that goes in service layer)
    - Handle HTTP requests (that's API layer)
    - Validate user permissions (that's API layer)
    """
    
    def __init__(self, engine: Optional[Engine] = None):
        """
        Initialize repository with database engine
        
        Args:
            engine: SQLAlchemy engine. If None, uses get_engine()
        
        Why dependency injection?
        - Testing: Can pass mock engine
        - Flexibility: Can use different databases
        """
        self.engine = engine or get_engine()
    
    # ==========================================================================
    # CREATE OPERATIONS
    # ==========================================================================
    
    def create_report(
        self, 
        user_id: str, 
        request: SaveReportRequest
    ) -> int:
        """
        Save a new report to database
        
        Args:
            user_id: Who is saving this report
            request: Validated report data from Pydantic model
        
        Returns:
            report_id: ID of newly created report
        
        Raises:
            Exception: If database operation fails
        
        Example:
            repo = ReportRepository()
            request = SaveReportRequest(
                report_name="My Report",
                user_question="Show sales",
                generated_sql="SELECT ..."
            )
            report_id = repo.create_report("user123", request)
            print(f"Created report {report_id}")
        """
        
        # SQL with placeholders (:param_name) - SAFE from SQL injection
        query = text("""
            INSERT INTO analytics_llm.saved_reports 
            (user_id, report_name, report_description, user_question, generated_sql, tags)
            VALUES (:user_id, :name, :description, :question, :sql, :tags)
            RETURNING report_id
        """)
        
        try:
            # Execute with parameterized values
            with self.engine.connect() as conn:
                result = conn.execute(
                    query,
                    {
                        "user_id": user_id,
                        "name": request.report_name,
                        "description": request.report_description,
                        "question": request.user_question,
                        "sql": request.generated_sql,
                        "tags": request.tags or []
                    }
                )
                # Commit the transaction
                conn.commit()
                
                # Get the generated report_id
                report_id = result.fetchone()[0]
                
                logger.info(f"Created report {report_id} for user {user_id}")
                return report_id
                
        except Exception as e:
            logger.error(f"Failed to create report: {e}")
            raise
    
    # ==========================================================================
    # READ OPERATIONS
    # ==========================================================================
    
    def get_report_by_id(
        self, 
        report_id: int, 
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single report by ID
        
        Security: Always checks user_id to prevent unauthorized access
        User can only see their own reports!
        
        Args:
            report_id: Report to fetch
            user_id: Who is requesting (for security)
        
        Returns:
            Dictionary with report data, or None if not found/no access
        
        Example:
            report = repo.get_report_by_id(42, "user123")
            if report:
                print(report['report_name'])
            else:
                print("Not found or no access")
        """
        
        query = text("""
            SELECT 
                report_id,
                user_id,
                report_name,
                report_description,
                user_question,
                generated_sql,
                created_at,
                updated_at,
                last_executed_at,
                execution_count,
                is_favorite,
                tags,
                status
            FROM analytics_llm.saved_reports
            WHERE report_id = :report_id 
              AND user_id = :user_id  -- 🔒 Security check!
              AND status = 'active'    -- Don't show deleted reports
        """)
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    query,
                    {"report_id": report_id, "user_id": user_id}
                )
                row = result.fetchone()
                
                if row:
                    # Convert SQLAlchemy Row to dictionary
                    return dict(row._mapping)
                return None
                
        except Exception as e:
            logger.error(f"Failed to fetch report {report_id}: {e}")
            raise
    
    def get_user_reports(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        favorite_only: bool = False,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all reports for a user (paginated)
        
        Args:
            user_id: User whose reports to fetch
            limit: Max number of reports to return (pagination)
            offset: Skip this many reports (pagination)
            favorite_only: Only return favorited reports
            tags: Filter by these tags (AND logic)
        
        Returns:
            List of report dictionaries
        
        Example:
            # Get page 1 (reports 0-19)
            page1 = repo.get_user_reports("user123", limit=20, offset=0)
            
            # Get page 2 (reports 20-39)
            page2 = repo.get_user_reports("user123", limit=20, offset=20)
            
            # Get only favorites
            favs = repo.get_user_reports("user123", favorite_only=True)
            
            # Get reports tagged 'sales'
            sales = repo.get_user_reports("user123", tags=['sales'])
        """
        
        # Build dynamic query based on filters
        where_clauses = ["user_id = :user_id", "status = 'active'"]
        params = {
            "user_id": user_id,
            "limit": limit,
            "offset": offset
        }
        
        if favorite_only:
            where_clauses.append("is_favorite = TRUE")
        
        if tags:
            # PostgreSQL array contains operator
            # Check if ALL provided tags are in the report's tags array
            where_clauses.append("tags @> :tags")
            params["tags"] = tags
        
        where_sql = " AND ".join(where_clauses)
        
        query = text(f"""
            SELECT 
                report_id,
                report_name,
                created_at,
                last_executed_at,
                execution_count,
                is_favorite,
                tags
            FROM analytics_llm.saved_reports
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(query, params)
                rows = [dict(row._mapping) for row in result]
                
                logger.info(f"Fetched {len(rows)} reports for user {user_id}")
                return rows
                
        except Exception as e:
            logger.error(f"Failed to fetch reports for user {user_id}: {e}")
            raise
    
    def count_user_reports(self, user_id: str) -> int:
        """
        Count total number of reports for a user
        
        Used for pagination: "Showing 20 of 156 reports"
        
        Args:
            user_id: User to count reports for
        
        Returns:
            Total number of active reports
        """
        
        query = text("""
            SELECT COUNT(*) 
            FROM analytics_llm.saved_reports
            WHERE user_id = :user_id AND status = 'active'
        """)
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(query, {"user_id": user_id})
                count = result.scalar()  # Get single value
                return count
                
        except Exception as e:
            logger.error(f"Failed to count reports: {e}")
            raise
    
    def search_reports(
        self,
        user_id: str,
        search_term: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search reports by name (full-text search)
        
        Uses PostgreSQL's full-text search (remember our GIN index?)
        
        Args:
            user_id: User whose reports to search
            search_term: What to search for (e.g., "sales report")
            limit: Max results
        
        Returns:
            List of matching reports, ranked by relevance
        
        Example:
            results = repo.search_reports("user123", "sales customer")
            # Returns reports with "sales" AND "customer" in name
        """
        
        query = text("""
            SELECT 
                report_id,
                report_name,
                created_at,
                last_executed_at,
                execution_count,
                is_favorite,
                tags,
                ts_rank(
                    to_tsvector('english', report_name),
                    to_tsquery('english', :search_term)
                ) as relevance
            FROM analytics_llm.saved_reports
            WHERE user_id = :user_id 
              AND status = 'active'
              AND to_tsvector('english', report_name) @@ to_tsquery('english', :search_term)
            ORDER BY relevance DESC, created_at DESC
            LIMIT :limit
        """)
        
        # Convert "sales report" → "sales & report" for full-text search
        search_query = ' & '.join(search_term.split())
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    query,
                    {
                        "user_id": user_id,
                        "search_term": search_query,
                        "limit": limit
                    }
                )
                return [dict(row._mapping) for row in result]
                
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    # ==========================================================================
    # UPDATE OPERATIONS
    # ==========================================================================
    
    def update_report(
        self,
        report_id: int,
        user_id: str,
        updates: UpdateReportRequest
    ) -> bool:
        """
        Update report metadata (name, description, tags, favorite)
        
        Only updates fields that are provided (partial update)
        
        Args:
            report_id: Report to update
            user_id: Who is updating (security check)
            updates: Fields to update (only non-None fields are updated)
        
        Returns:
            True if updated, False if not found/no access
        
        Example:
            # Only update name
            updated = repo.update_report(
                42, 
                "user123",
                UpdateReportRequest(report_name="New Name")
            )
            
            # Update multiple fields
            updated = repo.update_report(
                42,
                "user123", 
                UpdateReportRequest(
                    report_name="New Name",
                    is_favorite=True,
                    tags=["sales", "updated"]
                )
            )
        """
        
        # Build dynamic UPDATE statement for provided fields only
        update_fields = []
        params = {"report_id": report_id, "user_id": user_id}
        
        if updates.report_name is not None:
            update_fields.append("report_name = :report_name")
            params["report_name"] = updates.report_name
        
        if updates.report_description is not None:
            update_fields.append("report_description = :report_description")
            params["report_description"] = updates.report_description
        
        if updates.tags is not None:
            update_fields.append("tags = :tags")
            params["tags"] = updates.tags
        
        if updates.is_favorite is not None:
            update_fields.append("is_favorite = :is_favorite")
            params["is_favorite"] = updates.is_favorite
        
        # Always update timestamp
        update_fields.append("updated_at = NOW()")
        
        if not update_fields:
            # Nothing to update
            return False
        
        update_sql = ", ".join(update_fields)
        
        query = text(f"""
            UPDATE analytics_llm.saved_reports
            SET {update_sql}
            WHERE report_id = :report_id 
              AND user_id = :user_id
              AND status = 'active'
            RETURNING report_id
        """)
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(query, params)
                conn.commit()
                
                # Check if any row was updated
                updated = result.rowcount > 0
                
                if updated:
                    logger.info(f"Updated report {report_id}")
                else:
                    logger.warning(f"Report {report_id} not found or no access")
                
                return updated
                
        except Exception as e:
            logger.error(f"Failed to update report {report_id}: {e}")
            raise
    
    def update_execution_stats(
        self,
        report_id: int,
        execution_time_ms: Optional[int] = None
    ) -> None:
        """
        Update execution statistics after running a report
        
        Increments execution_count and updates last_executed_at
        
        Args:
            report_id: Report that was executed
            execution_time_ms: How long query took (optional)
        
        Called automatically after executing a report
        """
        
        query = text("""
            UPDATE analytics_llm.saved_reports
            SET 
                last_executed_at = NOW(),
                execution_count = execution_count + 1,
                updated_at = NOW()
            WHERE report_id = :report_id
        """)
        
        try:
            with self.engine.connect() as conn:
                conn.execute(query, {"report_id": report_id})
                conn.commit()
                logger.info(f"Updated execution stats for report {report_id}")
                
        except Exception as e:
            # Don't fail the request if stats update fails
            logger.error(f"Failed to update execution stats: {e}")
    
    # ==========================================================================
    # DELETE OPERATIONS
    # ==========================================================================
    
    def delete_report(
        self,
        report_id: int,
        user_id: str,
        soft_delete: bool = True
    ) -> bool:
        """
        Delete a report
        
        Args:
            report_id: Report to delete
            user_id: Who is deleting (security check)
            soft_delete: If True, mark as deleted; if False, actually delete
        
        Returns:
            True if deleted, False if not found/no access
        
        Soft delete vs Hard delete:
        - Soft: Status set to 'deleted', data preserved (can restore later)
        - Hard: Row actually deleted from database (permanent)
        
        Recommendation: Use soft delete in production for audit trail
        """
        
        if soft_delete:
            # Mark as deleted (can restore later)
            query = text("""
                UPDATE analytics_llm.saved_reports
                SET status = 'deleted', updated_at = NOW()
                WHERE report_id = :report_id 
                  AND user_id = :user_id
                  AND status = 'active'
                RETURNING report_id
            """)
        else:
            # Actually delete (CASCADE will delete executions too)
            query = text("""
                DELETE FROM analytics_llm.saved_reports
                WHERE report_id = :report_id 
                  AND user_id = :user_id
                RETURNING report_id
            """)
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    query,
                    {"report_id": report_id, "user_id": user_id}
                )
                conn.commit()
                
                deleted = result.rowcount > 0
                
                if deleted:
                    delete_type = "soft" if soft_delete else "hard"
                    logger.info(f"{delete_type} deleted report {report_id}")
                else:
                    logger.warning(f"Report {report_id} not found or no access")
                
                return deleted
                
        except Exception as e:
            logger.error(f"Failed to delete report {report_id}: {e}")
            raise
    
    # ==========================================================================
    # EXECUTION HISTORY
    # ==========================================================================
    
    def log_execution(
        self,
        report_id: int,
        user_id: str,
        execution_time_ms: int,
        row_count: int,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log a report execution to history table
        
        Used for:
        - Audit trail (who ran what, when)
        - Performance monitoring (slow queries)
        - Usage analytics (most popular reports)
        
        Args:
            report_id: Which report was executed
            user_id: Who executed it
            execution_time_ms: Query duration
            row_count: Number of rows returned
            error_message: If execution failed, error details
        """
        
        query = text("""
            INSERT INTO analytics_llm.report_executions
            (report_id, user_id, execution_time_ms, row_count, error_message)
            VALUES (:report_id, :user_id, :exec_time, :row_count, :error)
        """)
        
        try:
            with self.engine.connect() as conn:
                conn.execute(
                    query,
                    {
                        "report_id": report_id,
                        "user_id": user_id,
                        "exec_time": execution_time_ms,
                        "row_count": row_count,
                        "error": error_message
                    }
                )
                conn.commit()
                
        except Exception as e:
            # Don't fail the request if logging fails
            logger.error(f"Failed to log execution: {e}")
    
    def get_execution_history(
        self,
        report_id: int,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent execution history for a report
        
        Args:
            report_id: Report to get history for
            user_id: Security check
            limit: Number of recent executions to return
        
        Returns:
            List of execution records
        
        Use case: Show user "You ran this report 5 times, 
                  last time returned 10 rows in 45ms"
        """
        
        query = text("""
            SELECT 
                e.execution_id,
                e.executed_at,
                e.execution_time_ms,
                e.row_count,
                e.error_message
            FROM analytics_llm.report_executions e
            JOIN analytics_llm.saved_reports r 
                ON e.report_id = r.report_id
            WHERE e.report_id = :report_id 
              AND r.user_id = :user_id
            ORDER BY e.executed_at DESC
            LIMIT :limit
        """)
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    query,
                    {
                        "report_id": report_id,
                        "user_id": user_id,
                        "limit": limit
                    }
                )
                return [dict(row._mapping) for row in result]
                
        except Exception as e:
            logger.error(f"Failed to fetch execution history: {e}")
            raise


# ==============================================================================
# SINGLETON INSTANCE (convenience)
# ==============================================================================

# Create a single instance to reuse across the application
_report_repository = None

def get_report_repository() -> ReportRepository:
    """
    Get or create repository instance
    
    Singleton pattern: Only one instance exists
    
    Usage:
        from report_repository import get_report_repository
        
        repo = get_report_repository()
        report = repo.get_report_by_id(42, "user123")
    """
    global _report_repository
    if _report_repository is None:
        _report_repository = ReportRepository()
    return _report_repository

