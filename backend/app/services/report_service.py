"""
Report Service

This service manages saved reports (queries that users can save and execute later).

Responsibilities:
1. Save reports (from query results or manually)
2. Retrieve reports by ID
3. List user's reports (with pagination)
4. Search reports (by name, question, description)
5. Update reports
6. Delete reports (soft delete)
7. Execute saved SQL queries

Flow:
User wants to save a query → ReportService → ReportRepository → Database
User wants to execute saved query → ReportService → QueryService → Results
"""

from datetime import datetime, timezone
from typing import List, Tuple, Optional, Dict, Any

from app.core.models.report import Report
from app.core.models.query import QueryResult
from app.core.exceptions import ReportNotFoundError, UnauthorizedAccessError
from app.repositories.base import ReportRepository
from app.config import get_logger

logger = get_logger(__name__)


class ReportService:
    """
    Service for managing saved reports.
    
    This service orchestrates report operations:
    - CRUD operations (Create, Read, Update, Delete)
    - Search functionality
    - Executing saved queries
    """
    
    def __init__(
        self,
        report_repository: ReportRepository,
    ):
        """
        Initialize ReportService with dependencies.
        
        Args:
            report_repository: Repository for report data access
        
        Why dependency injection?
        - Easy to test (can pass mock repository)
        - Easy to swap implementations
        - Clear dependencies
        """
        self.report_repository = report_repository
    
    async def save_report(
        self,
        report: Report,
    ) -> int:
        """
        Save a new report.
        
        Flow:
        ReportService
            ↓ receives
        Report (domain model)
            ↓ validates
        Report (already validated by domain model)
            ↓ calls
        ReportRepository.save_report()
            ↓ saves to
        Database
            ↓ returns
        report_id (int)
        
        Args:
            report: Report domain model to save
        
        Returns:
            int: The ID of the saved report
        
        Raises:
            ValueError: If report validation fails
        """
        logger.info(f"Saving report: {report.report_name} for user {report.user_id}")
        
        # Report is already validated by domain model (__post_init__)
        # Just save it through repository
        report_id = await self.report_repository.save_report(report)
        
        logger.info(f"Report saved with ID: {report_id}")
        return report_id
    
    async def save_report_from_query(
        self,
        query_result: QueryResult,
        report_name: str,
        user_id: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> int:
        """
        Save a report from a query result.
        
        This is a convenience method that creates a Report from QueryResult.
        
        Flow:
        QueryResult (from QueryService)
            ↓ extract
        question, sql
            ↓ create
        Report (domain model)
            ↓ save
        ReportRepository
            ↓ returns
        report_id
        
        Args:
            query_result: QueryResult from QueryService
            report_name: Name for the saved report
            user_id: User who owns the report
            description: Optional description
            tags: Optional tags
        
        Returns:
            int: The ID of the saved report
        """
        logger.info(f"Creating report from query result: {report_name}")
        
        # Create Report domain model from QueryResult
        report = Report(
            report_id=0,  # Will be set by database
            report_name=report_name,
            user_question=query_result.query.question,
            generated_sql=query_result.query.sql,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            report_description=description,
            tags=tags or [],
            execution_count=0,  # New report, not executed yet
        )
        
        # Save through repository
        return await self.save_report(report)
    
    async def get_report(
        self,
        report_id: int,
        user_id: str,
    ) -> Report:
        """
        Get a report by ID.
        
        Flow:
        ReportService
            ↓ calls
        ReportRepository.get_report(report_id, user_id)
            ↓ queries
        Database
            ↓ returns
        Report (domain model) or None
            ↓ checks
        If None → Raise ReportNotFoundError
        If found → Return Report
        
        Args:
            report_id: ID of the report
            user_id: User requesting the report (for authorization)
        
        Returns:
            Report: The report domain model
        
        Raises:
            ReportNotFoundError: If report not found or user doesn't have access
        """
        logger.debug(f"Getting report {report_id} for user {user_id}")
        
        report = await self.report_repository.get_report(report_id, user_id)
        
        if not report:
            logger.warning(f"Report {report_id} not found for user {user_id}")
            raise ReportNotFoundError(f"Report {report_id} not found")
        
        logger.debug(f"Report {report_id} retrieved successfully")
        return report
    
    async def list_reports(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Report], int]:
        """
        List reports for a user with pagination.
        
        Flow:
        ReportService
            ↓ calls
        ReportRepository.list_reports(user_id, limit, offset)
            ↓ queries
        Database (with pagination)
            ↓ returns
        (List[Report], total_count)
        
        Args:
            user_id: User to list reports for
            limit: Maximum number of reports to return
            offset: Number of reports to skip (for pagination)
        
        Returns:
            Tuple[List[Report], int]: List of reports and total count
        """
        logger.debug(f"Listing reports for user {user_id} (limit={limit}, offset={offset})")
        
        reports, total = await self.report_repository.list_reports(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
        
        logger.debug(f"Found {len(reports)} reports (total: {total})")
        return reports, total
    
    async def search_reports(
        self,
        user_id: str,
        query: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Report], int]:
        """
        Search reports by name, question, or description.
        
        Flow:
        ReportService
            ↓ calls
        ReportRepository.search_reports(user_id, query, limit, offset)
            ↓ queries
        Database (with ILIKE search)
            ↓ returns
        (List[Report], total_count)
        
        Args:
            user_id: User to search reports for
            query: Search term
            limit: Maximum number of reports to return
            offset: Number of reports to skip
        
        Returns:
            Tuple[List[Report], int]: List of matching reports and total count
        """
        logger.debug(f"Searching reports for user {user_id}: '{query}'")
        
        reports, total = await self.report_repository.search_reports(
            user_id=user_id,
            query=query,
            limit=limit,
            offset=offset,
        )
        
        logger.debug(f"Found {len(reports)} matching reports (total: {total})")
        return reports, total
    
    async def update_report(
        self,
        report_id: int,
        user_id: str,
        updated_report: Report,
    ) -> bool:
        """
        Update a report.
        
        Flow:
        ReportService
            ↓ validates
        Check report exists and user has access
            ↓ calls
        ReportRepository.update_report()
            ↓ updates
        Database
            ↓ returns
        bool (success)
        
        Args:
            report_id: ID of the report to update
            user_id: User requesting the update (for authorization)
            updated_report: Updated report domain model
        
        Returns:
            bool: True if updated successfully
        
        Raises:
            ReportNotFoundError: If report not found or user doesn't have access
        """
        logger.info(f"Updating report {report_id} for user {user_id}")
        
        # First, verify report exists and user has access
        existing_report = await self.get_report(report_id, user_id)
        
        # Ensure report_id matches
        if updated_report.report_id != report_id:
            raise ValueError(f"Report ID mismatch: {report_id} != {updated_report.report_id}")
        
        # Ensure user_id matches
        if updated_report.user_id != user_id:
            raise UnauthorizedAccessError("Cannot change report owner")
        
        # Update through repository
        success = await self.report_repository.update_report(
            report_id=report_id,
            user_id=user_id,
            updated=updated_report,
        )
        
        if success:
            logger.info(f"Report {report_id} updated successfully")
        else:
            logger.warning(f"Report {report_id} update failed")
        
        return success
    
    async def delete_report(
        self,
        report_id: int,
        user_id: str,
    ) -> bool:
        """
        Delete a report (soft delete).
        
        Flow:
        ReportService
            ↓ validates
        Check report exists and user has access
            ↓ calls
        ReportRepository.delete_report()
            ↓ soft deletes
        Database (sets status = 'deleted')
            ↓ returns
        bool (success)
        
        Args:
            report_id: ID of the report to delete
            user_id: User requesting the delete (for authorization)
        
        Returns:
            bool: True if deleted successfully
        
        Raises:
            ReportNotFoundError: If report not found or user doesn't have access
        """
        logger.info(f"Deleting report {report_id} for user {user_id}")
        
        # First, verify report exists and user has access
        await self.get_report(report_id, user_id)
        
        # Delete through repository (soft delete)
        success = await self.report_repository.delete_report(
            report_id=report_id,
            user_id=user_id,
        )
        
        if success:
            logger.info(f"Report {report_id} deleted successfully")
        else:
            logger.warning(f"Report {report_id} delete failed")
        
        return success
    
    async def execute_saved_report(
        self,
        report_id: int,
        user_id: str,
        max_rows: int = 500,
    ) -> Tuple[Report, List[Dict[str, Any]]]:
        """
        Execute a saved report's SQL query.
        
        Flow:
        ReportService
            ↓ gets
        Report (from repository)
            ↓ extracts
        SQL query
            ↓ calls
        ReportRepository.execute_saved_sql()
            ↓ executes
        Database query
            ↓ returns
        (Report, rows)
        
        Note: This uses the repository's execute_saved_sql method,
        which handles SQL execution directly. Alternatively, we could
        use QueryService here, but that would require regenerating SQL.
        
        Args:
            report_id: ID of the report to execute
            user_id: User requesting execution (for authorization)
            max_rows: Maximum rows to return
        
        Returns:
            Tuple[Report, List[Dict[str, Any]]]: Report and query results
        
        Raises:
            ReportNotFoundError: If report not found or user doesn't have access
        """
        logger.info(f"Executing saved report {report_id} for user {user_id}")
        
        # First, verify report exists and user has access
        await self.get_report(report_id, user_id)
        
        # Execute through repository
        report, rows = await self.report_repository.execute_saved_sql(
            report_id=report_id,
            user_id=user_id,
            max_rows=max_rows,
        )
        
        logger.info(f"Report {report_id} executed: {len(rows)} rows returned")
        return report, rows


