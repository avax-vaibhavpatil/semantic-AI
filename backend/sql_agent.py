# sql_agent.py
import os
import json
import logging
import time
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from prompts import PROMPT_SYSTEM, PROMPT_USER_TEMPLATE, ERROR_PROMPT
from sql_validator import validate_against_semantic, basic_sql_safety, check_query_results
from db_connector import run_select
from openai import OpenAI
import anthropic

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path, override=True) # Force .env to win over terminal
    logging.info(f"Loaded environment from {env_path}")

# ROOT CAUSE FIX: Wipe OpenAI key from memory to prevent library auto-detection
import os
os.environ.pop("OPENAI_API_KEY", None)

# Import report management components
from models import (
    SaveReportRequest,
    UpdateReportRequest,
    ExecuteReportRequest,
    ReportResponse,
    ReportListResponse,
    ReportListItem,
    ExecuteReportResponse,
    SaveReportResponse,
    DeleteReportResponse,
    database_row_to_report_response
)
from report_repository import get_report_repository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sql_agent")

SEMANTIC_JSON_PATH = os.environ.get("SEMANTIC_JSON", "backend/metadata/semantic.json")
try:
    with open(SEMANTIC_JSON_PATH, "r", encoding="utf-8") as f:
        SEMANTIC = json.load(f)
except Exception as e:
    logger.warning(f"Could not load semantic JSON at {SEMANTIC_JSON_PATH}: {e}")
    SEMANTIC = {}

# Configuration
preferred_ai = os.environ.get("PREFERRED_AI", "openai").lower()
groq_key = os.environ.get("GROQ_API_KEY")
openai_key = os.environ.get("OPENAI_API_KEY")
anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

# Set active provider and client
# Force Groq as primary for demo stability
if groq_key:
    ACTIVE_AI = "groq"
    client = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
    logger.info("🚀 ACTIVE AI: Groq (FORCED PRIMARY)")
# elif anthropic_key and preferred_ai == "claude":
#     ACTIVE_AI = "claude"
#     client = anthropic.Anthropic(api_key=anthropic_key)
#     logger.info("🚀 ACTIVE AI: Claude (Primary Preference)")
# elif openai_key and preferred_ai == "openai":
#     ACTIVE_AI = "openai"
#     client = OpenAI(api_key=openai_key)
#     logger.info("🚀 ACTIVE AI: OpenAI (Primary Preference)")
# ... (rest of logic commented out to prevent accidental OpenAI usage)
else:
    ACTIVE_AI = "none"
    client = None
    logger.error("❌ No API keys found for Groq")

app = FastAPI(title="AI Semantic SQL Agent")

@app.get("/health")
async def health():
    return {
        "ok": True, 
        "semantic_loaded": bool(SEMANTIC),
        "active_ai": ACTIVE_AI,
        "model": os.environ.get("ANTHROPIC_MODEL" if ACTIVE_AI == "claude" else "OPENAI_MODEL" if ACTIVE_AI == "openai" else "GROQ_MODEL")
    }

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    question: str
    max_rows: int = 500
    dialect: str = None

def call_openai_generate_sql(prompt_system: str, prompt_user: str, model: str = None) -> str:
    # PERMANENT FIX: Force Groq model for demo
    if not model:
        model = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
    
    # OpenAI-compatible API call (Using Groq client)
    messages = [
        {"role": "system", "content": prompt_system},
        {"role": "user", "content": prompt_user}
    ]
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.0,
        max_tokens=1500,
        n=1
    )
    text = resp.choices[0].message.content.strip()
    return text


def build_column_hints(semantic: dict) -> str:
    """
    Build a short, per-request hint for the LLM about which columns to prefer
    (e.g., prefer *_name when user asks for name, *_code when user asks for code/id).
    Keeps the main prompt short; derived from semantic.json metadata.
    """
    lines = []
    tables = semantic.get("tables", {})
    for tname, tmeta in tables.items():
        cols = tmeta.get("columns", {})
        names = [c for c, m in cols.items() if m.get("role") == "name"]
        codes = [c for c, m in cols.items() if m.get("role") in ("code", "id")]
        preferred_names = [c for c, m in cols.items() if m.get("preferred") and m.get("role") == "name"]
        if preferred_names:
            lines.append(f"- {tname}: prefer name columns {', '.join(preferred_names)} when user mentions name/title/person/handler.")
        elif names:
            lines.append(f"- {tname}: use name columns {', '.join(names)} when user mentions name/title/person/handler.")
        if codes:
            lines.append(f"- {tname}: use code/id columns {', '.join(codes)} when user explicitly asks for code/id/handled_by.")
    if not lines:
        return "- No additional column preferences."
    return "\n".join(lines)

@app.post("/ask")
async def ask(req: AskRequest):
    if ACTIVE_AI == "none":
        raise HTTPException(status_code=500, detail="No AI API keys configured (OpenAI or Groq)")

    sem_json_str = json.dumps(SEMANTIC)
    column_hints = build_column_hints(SEMANTIC)
    prompt_user = PROMPT_USER_TEMPLATE.format(
        semantic_json=sem_json_str,
        user_question=req.question,
        column_hints=column_hints
    )

    try:
        sql = call_openai_generate_sql(PROMPT_SYSTEM, prompt_user)
    except Exception as e:
        logger.exception("AI model call failed")
        raise HTTPException(status_code=500, detail=f"AI model error: {e}")

    if not basic_sql_safety(sql):
        raise HTTPException(status_code=400, detail="Generated SQL failed basic safety checks (not SELECT or contains forbidden tokens).")

    valid, msg = validate_against_semantic(sql, SEMANTIC)
    if not valid:
        raise HTTPException(status_code=400, detail=f"SQL validation failed: {msg}")

    try:
        rows = run_select(sql, max_rows=req.max_rows)
        
        # Validate results are meaningful (pass sql and semantic for date checking)
        results_valid, results_msg = check_query_results(rows, f"Query: {req.question}", sql=sql, semantic=SEMANTIC)
        if not results_valid:
            logger.warning(f"Query returned no meaningful data: {results_msg}")
            # Still return the data but with a warning
            return {"sql": sql, "rows": rows, "warning": results_msg}
        
        return {"sql": sql, "rows": rows}
    except Exception as e:
        logger.exception("SQL execution failed, attempting auto-fix")
        fix_prompt = ERROR_PROMPT.format(error=str(e), sql=sql)
        try:
            fixed_sql = call_openai_generate_sql(PROMPT_SYSTEM, fix_prompt)
        except Exception as e2:
            logger.exception("AI model fix attempt failed")
            raise HTTPException(status_code=500, detail=f"SQL execution error and fix attempt failed: {e2}")

        if not basic_sql_safety(fixed_sql):
            raise HTTPException(status_code=500, detail="Auto-fix produced unsafe SQL.")

        valid2, msg2 = validate_against_semantic(fixed_sql, SEMANTIC)
        if not valid2:
            raise HTTPException(status_code=500, detail=f"Auto-fix validation failed: {msg2}")

        try:
            rows = run_select(fixed_sql, max_rows=req.max_rows)
            
            # Validate results are meaningful (pass sql and semantic for date checking)
            results_valid, results_msg = check_query_results(rows, f"Query: {req.question}", sql=fixed_sql, semantic=SEMANTIC)
            if not results_valid:
                logger.warning(f"Fixed query returned no meaningful data: {results_msg}")
                return {"sql": fixed_sql, "rows": rows, "warning": results_msg}
            
            return {"sql": fixed_sql, "rows": rows}
        except Exception as e3:
            logger.exception("Fixed SQL execution failed")
            raise HTTPException(status_code=500, detail=f"Fixed SQL execution failed: {e3}")

@app.get("/health")
def health():
    return {"ok": True, "semantic_loaded": bool(SEMANTIC)}


# ==============================================================================
# AUTHENTICATION HELPER (Placeholder)
# ==============================================================================
# TODO: Replace with real authentication (JWT, OAuth, etc.)

def get_current_user_id() -> str:
    """
    Get current user ID from request
    
    For now, returns a demo user. In production, this would:
    1. Extract JWT token from Authorization header
    2. Validate the token
    3. Return user ID from token payload
    
    Example with JWT:
        from fastapi import Depends
        from fastapi.security import HTTPBearer
        
        security = HTTPBearer()
        
        def get_current_user_id(token: str = Depends(security)):
            payload = jwt.decode(token.credentials, SECRET_KEY)
            return payload['user_id']
    """
    # For development: single demo user
    # In production: extract from JWT/session
    return "demo_user"


# ==============================================================================
# REPORT MANAGEMENT ENDPOINTS
# ==============================================================================

@app.post("/reports/save", response_model=SaveReportResponse, tags=["Reports"])
async def save_report(request: SaveReportRequest):
    """
    Save a new report
    
    User flow:
    1. User asks question via /ask endpoint
    2. Gets results with SQL
    3. Clicks "Save Report" button
    4. Frontend shows modal for report name/description/tags
    5. User fills form and submits
    6. Frontend calls this endpoint
    7. Report saved to database
    
    Request body:
    ```json
    {
        "report_name": "My Sales Dashboard",
        "user_question": "Show top 10 customers by sales",
        "generated_sql": "SELECT ... LIMIT 10",
        "report_description": "Monthly sales leaders",
        "tags": ["sales", "monthly"]
    }
    ```
    
    Response:
    ```json
    {
        "report_id": 42,
        "message": "Report saved successfully"
    }
    ```
    """
    try:
        user_id = get_current_user_id()
        repo = get_report_repository()
        
        # Save to database
        report_id = repo.create_report(user_id, request)
        
        logger.info(f"User {user_id} saved report {report_id}: {request.report_name}")
        
        return SaveReportResponse(
            report_id=report_id,
            message="Report saved successfully"
        )
        
    except Exception as e:
        logger.exception("Failed to save report")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save report: {str(e)}"
        )


@app.get("/reports", response_model=ReportListResponse, tags=["Reports"])
async def list_reports(
    limit: int = Query(default=20, ge=1, le=100, description="Number of reports per page"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    favorite_only: bool = Query(default=False, description="Show only favorites"),
    tags: Optional[List[str]] = Query(default=None, description="Filter by tags")
):
    """
    Get list of user's saved reports (paginated)
    
    Query parameters:
    - limit: Reports per page (1-100, default 20)
    - offset: Skip this many reports (for pagination)
    - favorite_only: If true, only return favorited reports
    - tags: Filter by tags (e.g., ?tags=sales&tags=monthly)
    
    Examples:
    - GET /reports - First 20 reports
    - GET /reports?limit=50&offset=0 - First 50 reports
    - GET /reports?limit=20&offset=20 - Second page (reports 21-40)
    - GET /reports?favorite_only=true - Only favorites
    - GET /reports?tags=sales&tags=monthly - Reports with both tags
    
    Response:
    ```json
    {
        "reports": [
            {
                "report_id": 42,
                "report_name": "My Sales Dashboard",
                "created_at": "2025-12-15T10:30:00",
                "last_executed_at": "2025-12-15T11:45:00",
                "execution_count": 5,
                "is_favorite": false,
                "tags": ["sales", "monthly"]
            }
        ],
        "total": 156,
        "limit": 20,
        "offset": 0
    }
    ```
    """
    try:
        user_id = get_current_user_id()
        repo = get_report_repository()
        
        # Get reports from database
        reports_data = repo.get_user_reports(
            user_id=user_id,
            limit=limit,
            offset=offset,
            favorite_only=favorite_only,
            tags=tags
        )
        
        # Convert to Pydantic models
        reports = [ReportListItem(**report) for report in reports_data]
        
        # Get total count for pagination
        total = repo.count_user_reports(user_id)
        
        logger.info(f"User {user_id} listed reports: {len(reports)} of {total}")
        
        return ReportListResponse(
            reports=reports,
            total=total,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.exception("Failed to list reports")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list reports: {str(e)}"
        )


@app.get("/reports/search", response_model=ReportListResponse, tags=["Reports"])
async def search_reports(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(default=20, ge=1, le=100, description="Max results")
):
    """
    Search reports by name (full-text search)
    
    Query parameters:
    - q: Search term (e.g., "sales report")
    - limit: Maximum results to return
    
    Uses PostgreSQL full-text search for intelligent matching:
    - Matches word stems (e.g., "sales" matches "sale", "selling")
    - Ranks by relevance
    - Ignores common words (e.g., "the", "a")
    
    Examples:
    - GET /reports/search?q=sales - Find reports with "sales" in name
    - GET /reports/search?q=monthly%20report - Find "monthly" AND "report"
    
    Response: Same format as GET /reports (paginated list)
    
    Errors:
    - 400: Search query too short
    """
    try:
        user_id = get_current_user_id()
        repo = get_report_repository()
        
        # Search reports
        results = repo.search_reports(
            user_id=user_id,
            search_term=q,
            limit=limit
        )
        
        # Convert to Pydantic models
        reports = [ReportListItem(**report) for report in results]
        
        logger.info(f"User {user_id} searched for '{q}': {len(reports)} results")
        
        return ReportListResponse(
            reports=reports,
            total=len(reports),
            limit=limit,
            offset=0
        )
        
    except Exception as e:
        logger.exception("Search failed")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@app.get("/reports/{report_id}", response_model=ReportResponse, tags=["Reports"])
async def get_report(report_id: int):
    """
    Get detailed information about a specific report
    
    Path parameter:
    - report_id: ID of the report to fetch
    
    Returns full report details including SQL query
    
    Response:
    ```json
    {
        "report_id": 42,
        "report_name": "My Sales Dashboard",
        "user_question": "Show top 10 customers",
        "generated_sql": "SELECT ... LIMIT 10",
        "report_description": "Monthly sales leaders",
        "created_at": "2025-12-15T10:30:00",
        "updated_at": "2025-12-15T10:30:00",
        "last_executed_at": "2025-12-15T11:45:00",
        "execution_count": 5,
        "is_favorite": false,
        "tags": ["sales", "monthly"],
        "status": "active"
    }
    ```
    
    Errors:
    - 404: Report not found or user doesn't have access
    """
    try:
        user_id = get_current_user_id()
        repo = get_report_repository()
        
        # Get report from database (with security check)
        report_data = repo.get_report_by_id(report_id, user_id)
        
        if not report_data:
            raise HTTPException(
                status_code=404,
                detail=f"Report {report_id} not found or access denied"
            )
        
        # Convert to Pydantic model
        report = database_row_to_report_response(report_data)
        
        logger.info(f"User {user_id} fetched report {report_id}")
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to fetch report {report_id}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch report: {str(e)}"
        )


@app.post("/reports/{report_id}/execute", response_model=ExecuteReportResponse, tags=["Reports"])
async def execute_report(
    report_id: int,
    request: ExecuteReportRequest = ExecuteReportRequest()
):
    """
    Execute a saved report with fresh data
    
    This is the key feature: Run the saved SQL query to get updated results
    
    Path parameter:
    - report_id: ID of report to execute
    
    Request body (optional):
    ```json
    {
        "max_rows": 500
    }
    ```
    
    What happens:
    1. Fetch report from database
    2. Extract the SQL query
    3. Execute SQL against your data warehouse
    4. Return fresh results
    5. Update execution statistics
    6. Log execution history
    
    Response:
    ```json
    {
        "report": {
            "report_id": 42,
            "report_name": "My Sales Dashboard",
            ...
        },
        "rows": [
            {"customer": "ABC Corp", "sales": 50000},
            {"customer": "XYZ Ltd", "sales": 45000}
        ],
        "row_count": 10,
        "execution_time_ms": 45
    }
    ```
    
    Errors:
    - 404: Report not found
    - 500: SQL execution failed
    """
    start_time = time.time()
    
    try:
        user_id = get_current_user_id()
        repo = get_report_repository()
        
        # Get report (with security check)
        report_data = repo.get_report_by_id(report_id, user_id)
        
        if not report_data:
            raise HTTPException(
                status_code=404,
                detail=f"Report {report_id} not found or access denied"
            )
        
        # Extract SQL
        sql = report_data['generated_sql']
        
        logger.info(f"User {user_id} executing report {report_id}")
        
        # Execute SQL to get fresh data
        rows = run_select(sql, max_rows=request.max_rows)
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Update execution statistics
        repo.update_execution_stats(report_id, execution_time_ms)
        
        # Log execution history
        repo.log_execution(
            report_id=report_id,
            user_id=user_id,
            execution_time_ms=execution_time_ms,
            row_count=len(rows),
            error_message=None
        )
        
        # Get updated report data (with new execution stats)
        updated_report_data = repo.get_report_by_id(report_id, user_id)
        report = database_row_to_report_response(updated_report_data)
        
        logger.info(
            f"Report {report_id} executed successfully: "
            f"{len(rows)} rows in {execution_time_ms}ms"
        )
        
        return ExecuteReportResponse(
            report=report,
            rows=rows,
            row_count=len(rows),
            execution_time_ms=execution_time_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Log failed execution
        execution_time_ms = int((time.time() - start_time) * 1000)
        try:
            repo = get_report_repository()
            repo.log_execution(
                report_id=report_id,
                user_id=get_current_user_id(),
                execution_time_ms=execution_time_ms,
                row_count=0,
                error_message=str(e)
            )
        except:
            pass  # Don't fail if logging fails
        
        logger.exception(f"Failed to execute report {report_id}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute report: {str(e)}"
        )


@app.patch("/reports/{report_id}", response_model=ReportResponse, tags=["Reports"])
async def update_report(report_id: int, request: UpdateReportRequest):
    """
    Update report metadata (name, description, tags, favorite)
    
    Path parameter:
    - report_id: Report to update
    
    Request body (all fields optional):
    ```json
    {
        "report_name": "New Report Name",
        "report_description": "Updated description",
        "tags": ["sales", "updated"],
        "is_favorite": true
    }
    ```
    
    Only provided fields are updated. For example:
    - Send only {"is_favorite": true} to mark as favorite
    - Send only {"report_name": "New Name"} to rename
    
    Response: Updated report details
    
    Errors:
    - 404: Report not found or no access
    """
    try:
        user_id = get_current_user_id()
        repo = get_report_repository()
        
        # Update report (with security check)
        updated = repo.update_report(report_id, user_id, request)
        
        if not updated:
            raise HTTPException(
                status_code=404,
                detail=f"Report {report_id} not found or access denied"
            )
        
        # Get updated report
        report_data = repo.get_report_by_id(report_id, user_id)
        report = database_row_to_report_response(report_data)
        
        logger.info(f"User {user_id} updated report {report_id}")
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update report {report_id}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update report: {str(e)}"
        )


@app.delete("/reports/{report_id}", response_model=DeleteReportResponse, tags=["Reports"])
async def delete_report(
    report_id: int,
    hard_delete: bool = Query(default=False, description="Permanently delete (default: soft delete)")
):
    """
    Delete a report
    
    Path parameter:
    - report_id: Report to delete
    
    Query parameter:
    - hard_delete: If true, permanently delete. If false (default), soft delete
    
    Soft delete (default):
    - Report marked as deleted but data preserved
    - Can be restored later if needed
    - Recommended for production
    
    Hard delete:
    - Report permanently removed from database
    - Cannot be restored
    - Use with caution
    
    Examples:
    - DELETE /reports/42 - Soft delete (recommended)
    - DELETE /reports/42?hard_delete=true - Permanent deletion
    
    Response:
    ```json
    {
        "message": "Report deleted successfully",
        "deleted_report_id": 42
    }
    ```
    
    Errors:
    - 404: Report not found or no access
    """
    try:
        user_id = get_current_user_id()
        repo = get_report_repository()
        
        # Delete report (with security check)
        deleted = repo.delete_report(
            report_id=report_id,
            user_id=user_id,
            soft_delete=not hard_delete
        )
        
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Report {report_id} not found or access denied"
            )
        
        delete_type = "permanently deleted" if hard_delete else "deleted"
        logger.info(f"User {user_id} {delete_type} report {report_id}")
        
        return DeleteReportResponse(
            message=f"Report {delete_type} successfully",
            deleted_report_id=report_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete report {report_id}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete report: {str(e)}"
        )


# ==============================================================================
# EXECUTION HISTORY (Bonus endpoint)
# ==============================================================================

@app.get("/reports/{report_id}/history", tags=["Reports"])
async def get_execution_history(
    report_id: int,
    limit: int = Query(default=10, ge=1, le=50, description="Number of history records")
):
    """
    Get execution history for a report
    
    Shows recent times the report was run, with execution times and row counts
    
    Useful for:
    - Debugging ("Why is this report slow?")
    - Usage analytics ("How often is this report used?")
    - Audit trail ("Who ran this report?")
    
    Response:
    ```json
    [
        {
            "execution_id": 123,
            "executed_at": "2025-12-15T11:45:00",
            "execution_time_ms": 45,
            "row_count": 10,
            "error_message": null
        }
    ]
    ```
    """
    try:
        user_id = get_current_user_id()
        repo = get_report_repository()
        
        # Get history (with security check via JOIN)
        history = repo.get_execution_history(report_id, user_id, limit)
        
        logger.info(f"User {user_id} fetched history for report {report_id}")
        
        return history
        
    except Exception as e:
        logger.exception(f"Failed to fetch history for report {report_id}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch history: {str(e)}"
        )
