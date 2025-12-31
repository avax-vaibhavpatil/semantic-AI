"""
Report Routes

This module handles report management endpoints.

Routes:
- POST /api/v1/reports - Save a new report
- GET /api/v1/reports/{report_id} - Get a report by ID
- GET /api/v1/reports - List user's reports
- PUT /api/v1/reports/{report_id} - Update a report
- DELETE /api/v1/reports/{report_id} - Delete a report
- POST /api/v1/reports/{report_id}/execute - Execute a saved report
"""

from fastapi import APIRouter, Depends, Query, Path
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone

from app.core.models.report import Report
from app.services.report_service import ReportService
from app.config import get_logger

logger = get_logger(__name__)

# Create router for report endpoints
router = APIRouter(prefix="/reports", tags=["reports"])


# ============================================================
# REQUEST/RESPONSE MODELS (Pydantic)
# ============================================================

class SaveReportRequestModel(BaseModel):
    """
    Request model for saving a new report.
    
    This is what the frontend sends to save a report.
    """
    report_name: str = Field(..., description="Name of the report", min_length=1, max_length=200)
    user_question: str = Field(..., description="Original user question", min_length=1)
    generated_sql: str = Field(..., description="Generated SQL query", min_length=1)
    user_id: str = Field(..., description="User ID who owns the report", min_length=1)
    report_description: Optional[str] = Field(default=None, description="Optional description", max_length=1000)
    tags: Optional[List[str]] = Field(default=None, description="Optional tags")
    is_favorite: bool = Field(default=False, description="Mark as favorite")
    
    class Config:
        json_schema_extra = {
            "example": {
                "report_name": "Top 5 Customers by Sales",
                "user_question": "Show me top 5 customers by sales",
                "generated_sql": "SELECT customer_name, SUM(sales) FROM ...",
                "user_id": "user123",
                "report_description": "Monthly top customers report",
                "tags": ["sales", "customers", "top"],
                "is_favorite": True
            }
        }


class ReportResponseModel(BaseModel):
    """
    Response model for a single report.
    """
    success: bool
    report: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "report": {
                    "report_id": 1,
                    "report_name": "Top 5 Customers by Sales",
                    "user_question": "Show me top 5 customers by sales",
                    "generated_sql": "SELECT ...",
                    "user_id": "user123",
                    "created_at": "2025-12-30T10:00:00Z",
                    "updated_at": None,
                    "last_executed_at": None,
                    "execution_count": 0,
                    "is_favorite": True,
                    "report_description": "Monthly top customers report",
                    "tags": ["sales", "customers"],
                    "status": "active"
                }
            }
        }


class ListReportsResponseModel(BaseModel):
    """
    Response model for listing reports.
    """
    success: bool
    reports: List[dict]
    total: int
    limit: int
    offset: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "reports": [
                    {
                        "report_id": 1,
                        "report_name": "Top 5 Customers",
                        "user_question": "Show me top 5 customers",
                        "generated_sql": "SELECT ...",
                        "user_id": "user123",
                        "created_at": "2025-12-30T10:00:00Z",
                        "is_favorite": True,
                        "status": "active"
                    }
                ],
                "total": 10,
                "limit": 20,
                "offset": 0
            }
        }


class UpdateReportRequestModel(BaseModel):
    """
    Request model for updating a report.
    """
    report_name: Optional[str] = Field(default=None, description="New report name", max_length=200)
    report_description: Optional[str] = Field(default=None, description="New description", max_length=1000)
    tags: Optional[List[str]] = Field(default=None, description="New tags")
    is_favorite: Optional[bool] = Field(default=None, description="Favorite status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "report_name": "Updated Report Name",
                "report_description": "Updated description",
                "tags": ["updated", "tags"],
                "is_favorite": True
            }
        }


class ExecuteReportRequestModel(BaseModel):
    """
    Request model for executing a saved report.
    """
    max_rows: Optional[int] = Field(default=500, ge=1, le=10000, description="Maximum rows to return")
    
    class Config:
        json_schema_extra = {
            "example": {
                "max_rows": 100
            }
        }


class ExecuteReportResponseModel(BaseModel):
    """
    Response model for executing a saved report.
    """
    success: bool
    report: dict
    rows: List[dict]
    row_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "report": {
                    "report_id": 1,
                    "report_name": "Top 5 Customers",
                    "generated_sql": "SELECT ..."
                },
                "rows": [{"customer": "ABC", "sales": 1000}],
                "row_count": 1
            }
        }


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _report_to_dict(report: Report) -> dict:
    """
    Convert Report domain model to dictionary.
    
    Args:
        report: Report domain model
    
    Returns:
        dict: Dictionary representation of report
    """
    return {
        "report_id": report.report_id,
        "report_name": report.report_name,
        "user_question": report.user_question,
        "generated_sql": report.generated_sql,
        "user_id": report.user_id,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "updated_at": report.updated_at.isoformat() if report.updated_at else None,
        "last_executed_at": report.last_executed_at.isoformat() if report.last_executed_at else None,
        "execution_count": report.execution_count,
        "is_favorite": report.is_favorite,
        "report_description": report.report_description,
        "tags": report.tags,
        "status": report.status,
    }


# ============================================================
# DEPENDENCY INJECTION
# ============================================================

def get_report_service() -> ReportService:
    """
    Dependency function to get ReportService instance (singleton).
    
    CRITICAL: Returns pre-initialized service from dependency container.
    Does NOT create new instances - service is created once at app startup.
    
    Flow:
    FastAPI Request
        ↓ calls
    get_report_service()
        ↓ returns
    Pre-initialized ReportService (from dependency container)
    
    Why this approach?
    - Services created ONCE at startup (not per request)
    - Prevents creating heavy objects (repositories) on every request
    - Better performance and resource usage
    """
    from app.api.dependencies import get_report_service as get_service
    return get_service()


# ============================================================
# ROUTE 1: POST /api/v1/reports - Save Report
# ============================================================

@router.post("", response_model=ReportResponseModel, status_code=201)
async def save_report(
    request: SaveReportRequestModel,
    report_service: ReportService = Depends(get_report_service),
):
    """
    Save a new report.
    
    This endpoint allows users to save a query as a report for later use.
    
    Flow:
    Frontend Request (POST /api/v1/reports)
        ↓ receives
    SaveReportRequestModel (validated by Pydantic)
        ↓ converts
    Report (domain model)
        ↓ calls
    ReportService.save_report()
        ↓ saves to
    Database
        ↓ returns
    report_id
        ↓ converts
    ReportResponseModel (Pydantic)
        ↓ returns
    JSON Response to Frontend
    
    Args:
        request: SaveReportRequestModel from frontend
        report_service: ReportService (injected by FastAPI)
    
    Returns:
        ReportResponseModel: Saved report with ID
    
    Raises:
        HTTPException: If save fails (400, 500, etc.)
    """
    logger.info(f"Saving report: {request.report_name} for user {request.user_id}")
    
    # Step 1: Convert Pydantic model to domain model
    report = Report(
        report_id=0,  # Will be set by database
        report_name=request.report_name,
        user_question=request.user_question,
        generated_sql=request.generated_sql,
        user_id=request.user_id,
        created_at=datetime.now(timezone.utc),
        report_description=request.report_description,
        tags=request.tags or [],
        is_favorite=request.is_favorite,
        execution_count=0,
    )
    
    # Step 2: Save through service
    # Domain exceptions are caught by global exception handlers
    report_id = await report_service.save_report(report)
    
    # Step 3: Get the saved report (to return full details)
    saved_report = await report_service.get_report(report_id, request.user_id)
    
    # Step 4: Convert domain model to response model
    response = ReportResponseModel(
        success=True,
        report=_report_to_dict(saved_report),
    )
    
    logger.info(f"Report saved successfully with ID: {report_id}")
    return response


# ============================================================
# ROUTE 2: GET /api/v1/reports/{report_id} - Get Report
# ============================================================

@router.get("/{report_id}", response_model=ReportResponseModel)
async def get_report(
    report_id: int = Path(..., description="Report ID", gt=0),
    user_id: str = Query(..., description="User ID (for authorization)", min_length=1),
    report_service: ReportService = Depends(get_report_service),
):
    """
    Get a report by ID.
    
    This endpoint retrieves a specific report for a user.
    
    Flow:
    Frontend Request (GET /api/v1/reports/{report_id}?user_id=...)
        ↓ receives
    report_id (path parameter)
    user_id (query parameter)
        ↓ calls
    ReportService.get_report(report_id, user_id)
        ↓ queries
    Database
        ↓ returns
    Report (domain model)
        ↓ converts
    ReportResponseModel (Pydantic)
        ↓ returns
    JSON Response to Frontend
    
    Args:
        report_id: Report ID (path parameter)
        user_id: User ID (query parameter, for authorization)
        report_service: ReportService (injected by FastAPI)
    
    Returns:
        ReportResponseModel: Report details
    
    Raises:
        HTTPException: If report not found (404) or access denied (403)
    """
    logger.info(f"Getting report {report_id} for user {user_id}")
    
    # Get report through service
    # Domain exceptions are caught by global exception handlers
    report = await report_service.get_report(report_id, user_id)
    
    # Convert domain model to response model
    response = ReportResponseModel(
        success=True,
        report=_report_to_dict(report),
    )
    
    logger.info(f"Report {report_id} retrieved successfully")
    return response


# ============================================================
# ROUTE 3: GET /api/v1/reports - List Reports
# ============================================================

@router.get("", response_model=ListReportsResponseModel)
async def list_reports(
    user_id: str = Query(..., description="User ID", min_length=1),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of reports to return"),
    offset: int = Query(default=0, ge=0, description="Number of reports to skip (for pagination)"),
    search: Optional[str] = Query(default=None, description="Search term (searches name, question, description)"),
    report_service: ReportService = Depends(get_report_service),
):
    """
    List user's reports with pagination and optional search.
    
    This endpoint returns a paginated list of reports for a user.
    Optionally filters by search term.
    
    Flow:
    Frontend Request (GET /api/v1/reports?user_id=...&limit=...&offset=...)
        ↓ receives
    Query parameters (user_id, limit, offset, search?)
        ↓ calls
    ReportService.list_reports() or search_reports()
        ↓ queries
    Database (with pagination)
        ↓ returns
    (List[Report], total_count)
        ↓ converts
    ListReportsResponseModel (Pydantic)
        ↓ returns
    JSON Response to Frontend
    
    Args:
        user_id: User ID (query parameter)
        limit: Maximum number of reports to return
        offset: Number of reports to skip (for pagination)
        search: Optional search term
        report_service: ReportService (injected by FastAPI)
    
    Returns:
        ListReportsResponseModel: List of reports with pagination info
    
    Raises:
        HTTPException: If query fails (500, etc.)
    """
    logger.info(f"Listing reports for user {user_id} (limit={limit}, offset={offset}, search={search})")
    
    # If search term provided, use search_reports, otherwise use list_reports
    if search:
        reports, total = await report_service.search_reports(
            user_id=user_id,
            query=search,
            limit=limit,
            offset=offset,
        )
    else:
        reports, total = await report_service.list_reports(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
    
    # Convert domain models to dictionaries
    reports_dict = [_report_to_dict(report) for report in reports]
    
    # Convert to response model
    response = ListReportsResponseModel(
        success=True,
        reports=reports_dict,
        total=total,
        limit=limit,
        offset=offset,
    )
    
    logger.info(f"Listed {len(reports)} reports (total: {total})")
    return response


# ============================================================
# ROUTE 4: PUT /api/v1/reports/{report_id} - Update Report
# ============================================================

@router.put("/{report_id}", response_model=ReportResponseModel)
async def update_report(
    report_id: int = Path(..., description="Report ID", gt=0),
    user_id: str = Query(..., description="User ID (for authorization)", min_length=1),
    request: UpdateReportRequestModel = ...,
    report_service: ReportService = Depends(get_report_service),
):
    """
    Update a report.
    
    This endpoint allows users to update report metadata (name, description, tags, favorite status).
    
    Flow:
    Frontend Request (PUT /api/v1/reports/{report_id}?user_id=...)
        ↓ receives
    report_id (path parameter)
    user_id (query parameter)
    UpdateReportRequestModel (body)
        ↓ gets
    Existing Report (from database)
        ↓ merges
    Updated fields
        ↓ calls
    ReportService.update_report()
        ↓ updates
    Database
        ↓ returns
    Updated Report
        ↓ converts
    ReportResponseModel (Pydantic)
        ↓ returns
    JSON Response to Frontend
    
    Args:
        report_id: Report ID (path parameter)
        user_id: User ID (query parameter, for authorization)
        request: UpdateReportRequestModel with fields to update
        report_service: ReportService (injected by FastAPI)
    
    Returns:
        ReportResponseModel: Updated report
    
    Raises:
        HTTPException: If report not found (404) or access denied (403)
    """
    logger.info(f"Updating report {report_id} for user {user_id}")
    
    # Step 1: Get existing report
    existing_report = await report_service.get_report(report_id, user_id)
    
    # Step 2: Merge updates (only update fields that are provided)
    updated_report = Report(
        report_id=existing_report.report_id,
        report_name=request.report_name if request.report_name is not None else existing_report.report_name,
        user_question=existing_report.user_question,  # Cannot change question
        generated_sql=existing_report.generated_sql,  # Cannot change SQL
        user_id=existing_report.user_id,  # Cannot change user_id
        created_at=existing_report.created_at,
        updated_at=datetime.now(timezone.utc),  # Update timestamp
        last_executed_at=existing_report.last_executed_at,
        execution_count=existing_report.execution_count,
        is_favorite=request.is_favorite if request.is_favorite is not None else existing_report.is_favorite,
        report_description=request.report_description if request.report_description is not None else existing_report.report_description,
        tags=request.tags if request.tags is not None else existing_report.tags,
        status=existing_report.status,
    )
    
    # Step 3: Update through service
    # Domain exceptions are caught by global exception handlers
    await report_service.update_report(report_id, user_id, updated_report)
    
    # Step 4: Get updated report
    updated = await report_service.get_report(report_id, user_id)
    
    # Step 5: Convert to response model
    response = ReportResponseModel(
        success=True,
        report=_report_to_dict(updated),
    )
    
    logger.info(f"Report {report_id} updated successfully")
    return response


# ============================================================
# ROUTE 5: DELETE /api/v1/reports/{report_id} - Delete Report
# ============================================================

@router.delete("/{report_id}", response_model=dict)
async def delete_report(
    report_id: int = Path(..., description="Report ID", gt=0),
    user_id: str = Query(..., description="User ID (for authorization)", min_length=1),
    report_service: ReportService = Depends(get_report_service),
):
    """
    Delete a report (soft delete).
    
    This endpoint soft-deletes a report (sets status to 'deleted').
    The report is not permanently removed from the database.
    
    Flow:
    Frontend Request (DELETE /api/v1/reports/{report_id}?user_id=...)
        ↓ receives
    report_id (path parameter)
    user_id (query parameter)
        ↓ validates
    Check report exists and user has access
        ↓ calls
    ReportService.delete_report()
        ↓ soft deletes
    Database (sets status = 'deleted')
        ↓ returns
    Success response
    
    Args:
        report_id: Report ID (path parameter)
        user_id: User ID (query parameter, for authorization)
        report_service: ReportService (injected by FastAPI)
    
    Returns:
        dict: Success message
    
    Raises:
        HTTPException: If report not found (404) or access denied (403)
    """
    logger.info(f"Deleting report {report_id} for user {user_id}")
    
    # Delete through service
    # Domain exceptions are caught by global exception handlers
    success = await report_service.delete_report(report_id, user_id)
    
    if success:
        logger.info(f"Report {report_id} deleted successfully")
        return {
            "success": True,
            "message": f"Report {report_id} deleted successfully"
        }
    else:
        logger.warning(f"Report {report_id} delete failed")
        return {
            "success": False,
            "message": f"Failed to delete report {report_id}"
        }


# ============================================================
# ROUTE 6: POST /api/v1/reports/{report_id}/execute - Execute Saved Report
# ============================================================

@router.post("/{report_id}/execute", response_model=ExecuteReportResponseModel)
async def execute_saved_report(
    report_id: int = Path(..., description="Report ID", gt=0),
    user_id: str = Query(..., description="User ID (for authorization)", min_length=1),
    request: ExecuteReportRequestModel = ...,
    report_service: ReportService = Depends(get_report_service),
):
    """
    Execute a saved report's SQL query.
    
    This endpoint executes the SQL query stored in a saved report
    and returns the results.
    
    Flow:
    Frontend Request (POST /api/v1/reports/{report_id}/execute?user_id=...)
        ↓ receives
    report_id (path parameter)
    user_id (query parameter)
    ExecuteReportRequestModel (body, optional max_rows)
        ↓ validates
    Check report exists and user has access
        ↓ gets
    Report (with SQL query)
        ↓ executes
    SQL query on database
        ↓ returns
    Query results
        ↓ converts
    ExecuteReportResponseModel (Pydantic)
        ↓ returns
    JSON Response to Frontend
    
    Args:
        report_id: Report ID (path parameter)
        user_id: User ID (query parameter, for authorization)
        request: ExecuteReportRequestModel with optional max_rows
        report_service: ReportService (injected by FastAPI)
    
    Returns:
        ExecuteReportResponseModel: Report and query results
    
    Raises:
        HTTPException: If report not found (404) or query execution fails (500)
    """
    logger.info(f"Executing saved report {report_id} for user {user_id}")
    
    # Execute through service
    # Domain exceptions are caught by global exception handlers
    report, rows = await report_service.execute_saved_report(
        report_id=report_id,
        user_id=user_id,
        max_rows=request.max_rows,
    )
    
    # Convert to response model
    response = ExecuteReportResponseModel(
        success=True,
        report=_report_to_dict(report),
        rows=rows,
        row_count=len(rows),
    )
    
    logger.info(f"Report {report_id} executed successfully: {len(rows)} rows returned")
    return response

