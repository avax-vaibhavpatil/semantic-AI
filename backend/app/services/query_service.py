"""
Query Service

This service handles the core business logic for natural language queries:
1. Receives user's question
2. Loads semantic layer
3. Generates SQL using AI
4. Executes query on database
5. Returns results

Flow:
User Question → QueryService → SemanticRepository → AI Router → Database → Results
"""

from datetime import datetime, timezone
from typing import Dict, Any, List
import time
import asyncio

from app.core.models.query import QueryRequest, Query, QueryResult
from app.core.models.semantic import SemanticLayer
from app.core.exceptions import QueryValidationError, SQLGenerationError, SQLExecutionError
from app.repositories.base import SemanticRepository
from app.infrastructure.ai.router import ProviderRouter
from app.infrastructure.database.query_executor import execute_query
from app.config import get_logger, get_settings

logger = get_logger(__name__)


class QueryService:
    """
    Service for handling natural language queries.
    
    This is the main business logic that orchestrates:
    - Loading semantic layer
    - AI-powered SQL generation
    - Query execution
    - Result formatting
    """
    
    def __init__(
        self,
        semantic_repository: SemanticRepository,
        ai_router: ProviderRouter,
    ):
        """
        Initialize QueryService with dependencies.
        
        Args:
            semantic_repository: Repository to load semantic layer
            ai_router: Router for AI providers (with fallback)
        
        Why dependency injection?
        - Easy to test (can pass mock repositories)
        - Easy to swap implementations
        - Clear dependencies
        """
        self.semantic_repository = semantic_repository
        self.ai_router = ai_router
    
    async def execute_query(
        self,
        request: QueryRequest,
    ) -> QueryResult:
        """
        Execute a natural language query.
        
        This is the main method - the complete flow:
        
        Step 1: Load semantic layer (from repository)
        Step 2: Build AI prompt (system + user)
        Step 3: Generate SQL (using AI router)
        Step 4: Execute SQL (on database)
        Step 5: Format and return results
        
        Args:
            request: QueryRequest with user's question
        
        Returns:
            QueryResult with data and metadata
        
        Raises:
            QueryValidationError: If query is invalid
            Exception: Database or AI errors
        """
        start_time = time.time()
        logger.info(f"Executing query: {request.question[:50]}...")
        
        try:
            # ===================================================================
            # STEP 1: Load Semantic Layer
            # ===================================================================
            # The semantic layer tells AI what tables/columns are available
            logger.debug("Loading semantic layer...")
            semantic_layer = await self.semantic_repository.load_semantic()
            logger.debug(f"Semantic layer loaded: {len(semantic_layer.tables)} tables")
            
            # ===================================================================
            # STEP 2: Build AI Prompts
            # ===================================================================
            # System prompt: Instructions for AI
            # User prompt: User's question + semantic layer context
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(request.question, semantic_layer)
            
            logger.debug("Prompts built, generating SQL...")
            
            # ===================================================================
            # STEP 3: Generate SQL using AI (with timeout)
            # ===================================================================
            # AI router tries providers in order (Claude → Groq → OpenAI)
            # Falls back automatically on retryable errors
            # CRITICAL: Add timeout to prevent hanging requests
            settings = get_settings()
            ai_timeout = settings.ai_timeout_seconds
            
            # Run AI call in thread pool with timeout (AI providers are synchronous)
            loop = asyncio.get_event_loop()
            try:
                sql = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: self.ai_router.generate_sql(
                            system_prompt=system_prompt,
                            user_prompt=user_prompt,
                            temperature=0.0,  # Low temperature = deterministic
                            max_tokens=1500,  # Enough for complex queries
                        )
                    ),
                    timeout=ai_timeout,
                )
            except asyncio.TimeoutError:
                logger.error(f"AI SQL generation timed out after {ai_timeout}s")
                raise SQLGenerationError(f"Query generation timed out. Please try again with a simpler question.")
            
            logger.info(f"SQL generated: {sql[:100]}...")

            # Guardrail: prevent multiple top-level SELECT statements
            self._validate_single_statement(sql)
            
            # ===================================================================
            # STEP 4: Create Query Domain Model
            # ===================================================================
            # This represents the query in our domain
            query = Query(
                question=request.question,
                sql=sql,
                generated_at=datetime.now(timezone.utc),
            )
            
            # ===================================================================
            # STEP 5: Execute SQL on Database (with timeout)
            # ===================================================================
            logger.debug("Executing SQL on database...")
            execution_start = time.time()
            
            # CRITICAL: Add timeout to prevent hanging database queries
            sql_timeout = settings.sql_timeout_seconds
            
            try:
                rows = await asyncio.wait_for(
                    execute_query(
                        sql=sql,
                        max_rows=request.max_rows,
                    ),
                    timeout=sql_timeout,
                )
            except asyncio.TimeoutError:
                logger.error(f"SQL execution timed out after {sql_timeout}s")
                raise SQLExecutionError(f"Query execution timed out. The query may be too complex. Please try a simpler query.")
            except Exception as db_error:
                # Convert database errors to SQLExecutionError
                # This includes ProgrammingError, OperationalError, etc.
                error_msg = str(db_error)
                logger.error(f"Database error: {error_msg}")
                # Provide user-friendly error message
                if "does not exist" in error_msg or "UndefinedColumnError" in error_msg:
                    raise SQLExecutionError(
                        "The generated query references columns or tables that don't exist. "
                        "Please try rephrasing your question or be more specific about which table to use."
                    )
                else:
                    raise SQLExecutionError(
                        f"Database error: {error_msg[:200]}"  # Truncate long error messages
                    )
                
            execution_time_ms = (time.time() - execution_start) * 1000
            query.execution_time_ms = execution_time_ms
            
            logger.info(f"Query executed: {len(rows)} rows in {execution_time_ms:.2f}ms")
            
            # ===================================================================
            # STEP 6: Build and Return Result
            # ===================================================================
            total_time_ms = (time.time() - start_time) * 1000
            
            result = QueryResult(
                query=query,
                rows=rows,
                row_count=len(rows),
                execution_time_ms=execution_time_ms,
                executed_at=datetime.now(timezone.utc),
            )
            
            # Add warning if result was truncated
            if len(rows) >= request.max_rows:
                result.warning = f"Result truncated to {request.max_rows} rows"
                logger.warning(f"Result truncated: {len(rows)} rows returned")
            
            logger.info(f"Query completed in {total_time_ms:.2f}ms")
            return result
            
        except Exception as e:
            total_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Query failed after {total_time_ms:.2f}ms: {e}", exc_info=True)
            raise
    
    def _build_system_prompt(self) -> str:
        """
        Build the system prompt for AI.
        
        This tells AI how to generate SQL.
        System prompt = Instructions/guidelines
        """
        return """You are a SQL generator. Your task is to convert natural language questions into SQL queries.

Rules:
- Return ONLY a single SELECT statement (no explanations, no markdown)
- Use only tables and columns from the semantic layer provided
- Ensure queries are read-only (SELECT only, no INSERT/UPDATE/DELETE)
- Use proper SQL syntax
- Add LIMIT clause if not present
- CRITICAL: Do NOT include semicolon (;) in your SQL - LIMIT should come directly after ORDER BY
- Example CORRECT: SELECT ... ORDER BY column DESC LIMIT 5
- Example WRONG: SELECT ... ORDER BY column DESC; LIMIT 5

CRITICAL: TABLE AND COLUMN BOUNDARIES:
- Once you select a table, you MUST use ONLY columns from that specific table
- DO NOT mix columns from different tables in the same query
- Each table has its own column namespace:
  * stgw_* prefix = stock_gw table (stock gateway data)
  * spd_* prefix = stock_planning_data table
  * gws_* prefix = gwanalytics table
- If a column doesn't exist in the selected table, DO NOT use a similar column from another table
- CRITICAL: Before using ANY column, verify it exists in the selected table by checking the semantic layer
- If user mentions "stock gateway", "gateway", or uses terms like "ageing", "quality breakdown", prefer stock_gw table
- If user mentions "stock planning" or "planning", prefer stock_planning_data table
- Example: If querying stock_gw, use stgw_company_code, stgw_branch_code, stgw_stock_lvl_value
- Example: If querying stock_planning_data, use spd_company_code, spd_branch_code, spd_stock_level (NOT spd_stock_lvl_value - that doesn't exist!)
- Example: stock_planning_data does NOT have stgw_* columns - if user asks for "stock gateway" data, use stock_gw table
- Check the semantic layer to see which columns belong to which table before generating SQL

CRITICAL: USE SEMANTIC LAYER ALIASES:
- Each column in the semantic layer has an "aliases" array with alternative names
- ALWAYS match user's natural language terms to column aliases in the semantic layer
- Example: If user says "salesman", find the column whose aliases include "salesperson" or "handler"
- Example: If user says "customer", find the column whose aliases include "customer" or "client"
- The semantic layer aliases are your PRIMARY way to map natural language to SQL columns
- DO NOT guess column names - always use aliases from the semantic layer
- When matching aliases, ensure the column belongs to the table you've selected

CRITICAL NULL HANDLING:
- For "top N", "highest", "lowest", or any ORDER BY queries: ALWAYS filter NULLs on the sort column in WHERE clause
- Example: If ordering by sales DESC, use: WHERE sales IS NOT NULL ORDER BY sales DESC
- NEVER put NULLS LAST in WHERE clause - it only belongs in ORDER BY clause
- To handle NULLs in ORDER BY: ORDER BY column DESC NULLS LAST (not in WHERE clause)
- Example for "top 3 by sales": 
  SELECT ... FROM table WHERE sales_column IS NOT NULL ORDER BY sales_column DESC LIMIT 3
- This ensures meaningful data appears first, not NULL values
- Aggregations (SUM/AVG/COUNT) automatically ignore NULLs, so don't filter those unnecessarily"""
    
    def _build_user_prompt(
        self,
        question: str,
        semantic_layer: SemanticLayer,
    ) -> str:
        """
        Build the user prompt for AI.
        
        This includes:
        - User's question
        - Semantic layer context (what tables/columns are available)
        
        User prompt = Actual request + context
        """
        import json
        
        # Convert semantic layer to dict, then to JSON string for AI
        semantic_dict = semantic_layer.to_dict()
        semantic_json = json.dumps(semantic_dict, indent=2)
        
        return f"""Semantic Layer:
{semantic_json}

User Question: {question}

Generate a SQL query that answers the user's question using only the tables and columns defined in the semantic layer above."""

    def _validate_single_statement(self, sql: str) -> None:
        """
        Ensure the generated SQL contains only one top-level SELECT statement.

        Prevents concatenated multiple SELECTs (common when user asks two questions
        in one sentence) which cause syntax errors and are unsafe to run.
        """
        import re

        selects = re.findall(r"^\\s*select\\b", sql, flags=re.IGNORECASE | re.MULTILINE)
        if len(selects) > 1:
            raise SQLGenerationError(
                "Generated multiple SELECT statements; please ask one question at a time."
            )

