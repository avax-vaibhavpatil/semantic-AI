"""
Query Routes

This module handles natural language query endpoints.

Route: POST /api/v1/query
Purpose: Execute natural language queries and return SQL results
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional

from app.core.models.query import QueryRequest, QueryResult
from app.services.query_service import QueryService
from app.config import get_logger

logger = get_logger(__name__)

# Create router for query endpoints
router = APIRouter(prefix="/query", tags=["queries"])


# ============================================================
# REQUEST/RESPONSE MODELS (Pydantic)
# ============================================================

class QueryRequestModel(BaseModel):
    """
    Request model for natural language query.
    
    This is what the frontend sends to the API.
    """
    question: str = Field(..., description="Natural language question", min_length=1)
    max_rows: int = Field(default=500, ge=1, le=10000, description="Maximum rows to return")
    dialect: Optional[str] = Field(default=None, description="SQL dialect (optional)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Show me top 5 customers by sales",
                "max_rows": 100
            }
        }


class QueryResponseModel(BaseModel):
    """
    Response model for query execution.
    
    This is what the API returns to the frontend.
    """
    success: bool
    query: dict  # Query metadata (question, sql, etc.)
    rows: list  # Query results
    row_count: int
    execution_time_ms: float
    warning: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "query": {
                    "question": "Show me top 5 customers by sales",
                    "sql": "SELECT ...",
                    "generated_at": "2025-12-30T10:00:00Z"
                },
                "rows": [{"customer": "ABC", "sales": 1000}],
                "row_count": 1,
                "execution_time_ms": 123.45,
                "warning": None
            }
        }


# ============================================================
# DEPENDENCY INJECTION
# ============================================================

def get_query_service() -> QueryService:
    """
    Dependency function to get QueryService instance (singleton).
    
    CRITICAL: Returns pre-initialized service from dependency container.
    Does NOT create new instances - service is created once at app startup.
    
    Flow:
    FastAPI Request
        ↓ calls
    get_query_service()
        ↓ returns
    Pre-initialized QueryService (from dependency container)
    
    Why this approach?
    - Services created ONCE at startup (not per request)
    - Prevents creating heavy objects (repositories, AI providers) on every request
    - Better performance and resource usage
    """
    from app.api.dependencies import get_query_service as get_service
    return get_service()


# ============================================================
# ROUTE 1: POST /api/v1/query
# ============================================================

@router.post("", response_model=QueryResponseModel)
async def execute_query(
    request: QueryRequestModel,
    query_service: QueryService = Depends(get_query_service),
):
    """
    Execute a natural language query.
    
    This is the main endpoint for querying data using natural language.
    
    Flow:
    Frontend Request (POST /api/v1/query)
        ↓ receives
    QueryRequestModel (validated by Pydantic)
        ↓ converts
    QueryRequest (domain model)
        ↓ calls
    QueryService.execute_query()
        ↓ returns
    QueryResult (domain model)
        ↓ converts
    QueryResponseModel (Pydantic)
        ↓ returns
    JSON Response to Frontend
    
    Steps:
    1. Validate request (Pydantic does this automatically)
    2. Convert to domain model (QueryRequest)
    3. Call service (QueryService.execute_query)
    4. Handle errors (convert domain exceptions to HTTP)
    5. Convert result to response model
    6. Return JSON
    
    Args:
        request: QueryRequestModel from frontend
        query_service: QueryService (injected by FastAPI)
    
    Returns:
        QueryResponseModel: Query results and metadata
    
    Raises:
        HTTPException: If query fails (400, 500, etc.)
    """
    logger.info(f"Received query request: {request.question[:50]}...")
    
    # CRITICAL: No try/except here - global exception handlers catch domain exceptions
    # This keeps routes clean and ensures consistent error handling
    
    # Step 1: Convert Pydantic model to domain model
    query_request = QueryRequest(
        question=request.question,
        max_rows=request.max_rows,
        dialect=request.dialect,
    )
    
    # Step 2: Execute query through service
    # Domain exceptions are caught by global exception handlers
    query_result: QueryResult = await query_service.execute_query(query_request)
    
    # Step 3: Convert domain model to response model
    response = QueryResponseModel(
        success=True,
        query={
            "question": query_result.query.question,
            "sql": query_result.query.sql,
            "generated_at": query_result.query.generated_at.isoformat(),
            "execution_time_ms": query_result.query.execution_time_ms,
        },
        rows=query_result.rows,
        row_count=query_result.row_count,
        execution_time_ms=query_result.execution_time_ms,
        warning=query_result.warning,
    )
    
    logger.info(
        f"Query executed successfully: {query_result.row_count} rows in "
        f"{query_result.execution_time_ms:.2f}ms"
    )
    
    return response

