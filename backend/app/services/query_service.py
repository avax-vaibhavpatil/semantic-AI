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

CRITICAL NULL HANDLING:
- For "top N", "highest", "lowest", or any ORDER BY queries: ALWAYS filter NULLs on the sort column
- When using ORDER BY with DESC, add: WHERE sort_column IS NOT NULL OR use NULLS LAST
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

