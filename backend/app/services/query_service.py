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
from typing import Dict, Any, List, Optional
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
            # STEP 2: Detect Table from Question (Preprocessing)
            # ===================================================================
            # Pre-detect which table the user is asking about to enforce strict selection
            detected_table = self._detect_table_from_question(request.question, semantic_layer)
            
            # ===================================================================
            # STEP 3: Build AI Prompts
            # ===================================================================
            # System prompt: Instructions for AI
            # User prompt: User's question + semantic layer context + table enforcement
            system_prompt = self._build_system_prompt(detected_table)
            user_prompt = self._build_user_prompt(request.question, semantic_layer, detected_table)
            
            logger.debug("Prompts built, generating SQL...")
            
            # ===================================================================
            # STEP 4: Generate SQL using AI (with timeout)
            # ===================================================================
            # AI router uses Claude as primary provider
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
            
            # Guardrail: validate table selection if we detected one
            if detected_table:
                self._validate_table_selection(sql, detected_table)
                # Also validate that columns used exist in the selected table
                self._validate_columns_exist(sql, detected_table, semantic_layer)
            
            # ===================================================================
            # STEP 5: Create Query Domain Model
            # ===================================================================
            # This represents the query in our domain
            query = Query(
                question=request.question,
                sql=sql,
                generated_at=datetime.now(timezone.utc),
            )
            
            # ===================================================================
            # STEP 6: Execute SQL on Database (with timeout)
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
    
    def _detect_table_from_question(self, question: str, semantic_layer: SemanticLayer) -> Optional[str]:
        """
        Pre-detect which table the user is asking about by analyzing the semantic layer.
        
        This method reads the semantic layer and matches the question against:
        - Table descriptions
        - Column names
        - Column aliases
        - Column descriptions
        - Measures and dimensions
        
        Returns:
            Table key (e.g., "public.stock_gw") or None if ambiguous
        """
        question_lower = question.lower()
        question_words = set(question_lower.split())
        
        # High-priority keywords that strongly indicate specific tables
        table_indicators = {
            "public.stock_gw": [
                "stock gateway", "gateway", "ageing", "above 4 years",
                "0-6 months", "6-12 months", "1-2 years", "2-3 years", "3-4 years",
                "stgw_", "nos count", "quality breakdown"
            ],
            "public.stock_planning_data": [
                "stock planning", "planning", "reorder level", "reorder",
                "requirement", "requirements", "requirement based", "based on stock level",
                "stock level", "drum level", "pending order", "pending di", "pending st", "pending dd",
                "purchase order", "list price", "gross profit", "issue average", "pts average",
                "spd_", "stock transfer", "branch transfer", "below stock", "less than stock"
            ],
            "public.gwanalytics": [
                "gwanalytics", "gws_", "ytd sales", "year to date sales", "year-to-date sales",
                "budget", "customer", "handler", "salesperson", "salesman",
                "outstanding", "profit loss", "profit and loss", "last 90 days sales"
            ]
        }
        
        scores = {}
        
        # Analyze each table in the semantic layer
        for table_key, table in semantic_layer.tables.items():
            score = 0
            
            # 0. Check high-priority table indicators first (strongest signal)
            indicators = table_indicators.get(table_key, [])
            for indicator in indicators:
                if indicator in question_lower:
                    score += 30  # Very high weight for specific indicators
            
            # 1. Check table description
            if table.description:
                table_desc = table.description.lower()
                # Count matching words from question in table description
                desc_words = set(table_desc.split())
                matches = question_words.intersection(desc_words)
                score += len(matches) * 5  # High weight for description matches
            
            # 2. Check table name itself
            table_name_lower = table_key.lower()
            if table_key in question_lower or table_name_lower.replace("public.", "") in question_lower:
                score += 50  # Very high weight for explicit table mention
            
            # 3. Check column names and aliases
            for col_name, col in table.columns.items():
                col_name_lower = col_name.lower()
                
                # Check if column name appears in question
                if col_name_lower in question_lower:
                    score += 10  # High weight for column name match
                
                # Check column aliases
                for alias in col.aliases:
                    alias_lower = alias.lower()
                    if alias_lower in question_lower:
                        score += 8  # Good weight for alias match
                
                # Check column description
                if col.description:
                    col_desc = col.description.lower()
                    col_desc_words = set(col_desc.split())
                    col_matches = question_words.intersection(col_desc_words)
                    score += len(col_matches) * 3  # Medium weight for description matches
            
            # 4. Check measures and dimensions
            for measure in table.measures:
                measure_lower = str(measure).lower()
                if measure_lower in question_lower:
                    score += 7
            
            for dimension in table.dimensions:
                dimension_lower = str(dimension).lower()
                if dimension_lower in question_lower:
                    score += 7
            
            scores[table_key] = score
        
        # If we have a clear winner (score > 0 and at least 2x higher than others)
        if scores:
            max_score = max(scores.values())
            if max_score > 0:
                # Check if there's a clear winner
                winners = [k for k, v in scores.items() if v == max_score]
                if len(winners) == 1:
                    logger.debug(f"Table detected from semantic layer: {winners[0]} (score: {max_score})")
                    return winners[0]
                # If tied, prefer the one with highest score if it's significantly higher
                sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                if len(sorted_scores) >= 2:
                    if sorted_scores[0][1] >= sorted_scores[1][1] * 2:
                        logger.debug(f"Table detected from semantic layer: {sorted_scores[0][0]} (score: {sorted_scores[0][1]} vs {sorted_scores[1][1]})")
                        return sorted_scores[0][0]
                # If scores are close, log for debugging
                logger.debug(f"Ambiguous table selection. Scores: {scores}")
        
        logger.debug("No table detected from semantic layer analysis")
        return None
    
    def _build_system_prompt(self, detected_table: Optional[str] = None) -> str:
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
- CRITICAL: NEVER use bind parameters ($1, $2, :param, ?) - use literal values or omit filters if values not provided
- Example WRONG: WHERE company_code = :companyCode
- Example CORRECT: WHERE company_code = '03' (use actual value) or omit the filter if value not provided

CRITICAL: TABLE SELECTION - STRICT ENFORCEMENT:
- You MUST select the correct table based on the question. DO NOT guess or use the wrong table.
- If a specific table is detected from the question, you MUST use that table and ONLY that table.
- You have 3 main tables available. SELECT THE CORRECT ONE based on the question:
  1. **public.stock_gw** (columns: stgw_*)
     - Use for: Stock ageing (0-6 months, 6-12 months, 1-2 years, 2-3 years, 3-4 years, above 4 years)
     - Use for: Stock gateway data, stock valuation, stock value, stock quantity with ageing breakdown
     - Use for: Quality breakdown (drum, good, cut, small, scrap quantities)
     - Use for: NOS count, stock value by ageing buckets
     - Key indicators: "ageing", "above 4 years", "stock gateway", "stgw_*" columns
   
  2. **public.stock_planning_data** (columns: spd_*)
     - Use for: Stock planning, reorder levels, stock levels, drum levels
     - Use for: Pending orders (DI, ST, DD), purchase orders
     - Use for: List price, gross profit, issue averages, PTS averages
     - Use for: Stock transfers, branch transfers
     - Key indicators: "reorder", "planning", "pending orders", "stock level", "spd_*" columns
   
  3. **public.gwanalytics** (columns: gws_*)
     - Use for: Sales data (YTD sales, last year YTD sales, last 90 days sales)
     - Use for: Budget data, customer data, handler/salesperson data
     - Use for: Outstanding amounts, profit/loss
     - Key indicators: "sales", "budget", "customer", "handler", "salesperson", "gws_*" columns

- If user mentions "stock gateway" or "gateway" → use stock_gw
- If user mentions "planning" or "reorder" → use stock_planning_data
- If user mentions "sales" or "customer" or "handler" → use gwanalytics
- If ambiguous, check column prefixes in semantic layer - match the prefix pattern to the table
- CRITICAL: If the question mentions "stock gateway" or "gateway", you MUST use stock_gw table
- CRITICAL: If the question mentions "planning", "reorder", "requirement", "requirement based", or "based on stock level", you MUST use stock_planning_data table  
- CRITICAL: If the question mentions "sales" or "customer" or "handler", you MUST use gwanalytics table
- NEVER use stock_planning_data when the question asks about "stock gateway" or "gateway"
- NEVER use stock_gw when the question asks about "planning", "reorder", "requirement", or "reorder levels"
- NEVER use stock_gw when the question asks about "requirement based on stock level" - this MUST use stock_planning_data
- NEVER use stock_gw or stock_planning_data when the question asks about "sales" or "customer"

CRITICAL: TABLE AND COLUMN BOUNDARIES:
- Once you select a table, you MUST use ONLY columns from that specific table
- DO NOT mix columns from different tables in the same query
- Each table has its own column namespace (e.g., stgw_* for stock_gw, spd_* for stock_planning_data, gws_* for gwanalytics)
- If a column doesn't exist in the selected table, DO NOT use a similar column from another table
- Example: If querying stock_gw, use stgw_stock_qty, NOT spd_stock_level
- Example: If querying stock_planning_data, use spd_branch_code, NOT stgw_branch_code
- Example: If querying gwanalytics, use gws_company_code, NOT spd_company_code
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
- Aggregations (SUM/AVG/COUNT) automatically ignore NULLs, so don't filter those unnecessarily

CRITICAL: COALESCE TYPE MATCHING:
- When using COALESCE, ensure all arguments have compatible types
- If column is VARCHAR/TEXT, use COALESCE(column, '0') or COALESCE(column, '-') or COALESCE(column, '')
- If column is INTEGER/NUMERIC, use COALESCE(column, 0)
- Example WRONG: COALESCE(varchar_column, 0) - causes type mismatch error
- Example CORRECT: COALESCE(varchar_column, '0') or COALESCE(varchar_column, '-')
- Check data types in semantic layer before using COALESCE

CRITICAL: TABLE JOINS:
- ONLY join tables that exist in the semantic layer
- If a table is not in the semantic layer, DO NOT join it - use only columns from available tables
- If user requests data from missing tables, use only what's available in existing tables
- Example: If item/branch tables don't exist, use only stock_planning_data columns

CRITICAL: POSTGRESQL ROUND FUNCTION:
- PostgreSQL ROUND function requires NUMERIC type, not REAL
- For REAL columns, cast to NUMERIC first: ROUND(CAST(column AS NUMERIC), decimals)
- Example WRONG: ROUND(real_column, 1) - causes "function round(real, integer) does not exist"
- Example CORRECT: ROUND(CAST(real_column AS NUMERIC), 1)
- For INTEGER columns, ROUND works directly: ROUND(int_column) or ROUND(int_column, 0)
- Always cast REAL to NUMERIC before using ROUND with decimal places"""
    
    def _build_user_prompt(
        self,
        question: str,
        semantic_layer: SemanticLayer,
        detected_table: Optional[str] = None,
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
        
        # Add table enforcement if detected
        table_enforcement = ""
        if detected_table:
            table_name = detected_table.split(".")[-1] if "." in detected_table else detected_table
            table_enforcement = f"""

CRITICAL TABLE SELECTION ENFORCEMENT:
Based on the question, you MUST use the table: {detected_table}
- DO NOT use any other table
- Use ONLY columns from {detected_table} (prefix: {self._get_table_prefix(detected_table)})
- If the question asks for data that doesn't exist in {detected_table}, inform the user or use available columns
"""
        
        return f"""Semantic Layer:
{semantic_json}

User Question: {question}
{table_enforcement}
Generate a SQL query that answers the user's question using only the tables and columns defined in the semantic layer above."""
    
    def _get_table_prefix(self, table_key: str) -> str:
        """Get the column prefix for a table."""
        prefixes = {
            "public.stock_gw": "stgw_",
            "public.stock_planning_data": "spd_",
            "public.gwanalytics": "gws_"
        }
        return prefixes.get(table_key, "")

    def _validate_table_selection(self, sql: str, expected_table: str) -> None:
        """
        Validate that the generated SQL uses the expected table.
        
        Raises:
            SQLGenerationError: If wrong table is used
        """
        sql_upper = sql.upper()
        expected_table_upper = expected_table.upper().replace("PUBLIC.", "")
        
        # Check if expected table is in FROM clause
        if expected_table_upper not in sql_upper:
            # Check what table was actually used
            from_match = None
            if "FROM PUBLIC.STOCK_GW" in sql_upper:
                from_match = "stock_gw"
            elif "FROM PUBLIC.STOCK_PLANNING_DATA" in sql_upper:
                from_match = "stock_planning_data"
            elif "FROM PUBLIC.GWANALYTICS" in sql_upper:
                from_match = "gwanalytics"
            
            if from_match and from_match != expected_table_upper:
                raise SQLGenerationError(
                    f"Wrong table selected. Expected '{expected_table}' but got '{from_match}'. "
                    f"Please ensure the query uses the correct table based on the question."
                )
    
    def _validate_columns_exist(self, sql: str, table_key: str, semantic_layer: SemanticLayer) -> None:
        """
        Validate that all columns used in SQL actually exist in the selected table.
        
        Raises:
            SQLGenerationError: If non-existent columns are used
        """
        table = semantic_layer.get_table(table_key)
        if not table:
            return  # Table not found, let database handle the error
        
        # Extract column names from SQL (simple regex-based extraction)
        import re
        # Find all column references (word.word or just word after SELECT, WHERE, etc.)
        # This is a simple check - more sophisticated parsing could be added
        sql_upper = sql.upper()
        
        # Get expected prefix for this table
        expected_prefix = self._get_table_prefix(table_key)
        
        # Find potential column references with the expected prefix
        # Pattern: prefix followed by word characters
        prefix_pattern = re.compile(rf'\b{re.escape(expected_prefix.upper())}\w+', re.IGNORECASE)
        found_columns = set(prefix_pattern.findall(sql))
        
        # Check each found column exists in the table
        invalid_columns = []
        for col_ref in found_columns:
            col_name = col_ref.lower()
            # Remove prefix to get base column name
            if col_name.startswith(expected_prefix.lower()):
                base_name = col_name[len(expected_prefix):]
                # Check if column exists in table
                if not table.has_column(col_name):
                    # Also check without prefix (in case it's used differently)
                    if not table.has_column(base_name):
                        invalid_columns.append(col_ref)
        
        if invalid_columns:
            available_columns = list(table.columns.keys())[:10]  # Show first 10
            raise SQLGenerationError(
                f"Invalid columns used in query for table '{table_key}': {', '.join(invalid_columns)}. "
                f"These columns do not exist in the selected table. "
                f"Available columns include: {', '.join(available_columns)}..."
            )
    
    def _validate_columns_exist(self, sql: str, table_key: str, semantic_layer: SemanticLayer) -> None:
        """
        Validate that all columns used in SQL actually exist in the selected table.
        
        Raises:
            SQLGenerationError: If non-existent columns are used
        """
        table = semantic_layer.get_table(table_key)
        if not table:
            return  # Table not found, let database handle the error
        
        # Extract column names from SQL (simple regex-based extraction)
        import re
        # Get expected prefix for this table
        expected_prefix = self._get_table_prefix(table_key)
        
        # Find potential column references with the expected prefix
        # Pattern: prefix followed by word characters
        prefix_pattern = re.compile(rf'\b{re.escape(expected_prefix.lower())}\w+', re.IGNORECASE)
        found_columns = set(prefix_pattern.findall(sql))
        
        # Check each found column exists in the table
        invalid_columns = []
        for col_ref in found_columns:
            col_name = col_ref.lower()
            # Check if column exists in table
            if not table.has_column(col_name):
                invalid_columns.append(col_ref)
        
        if invalid_columns:
            available_columns = list(table.columns.keys())[:10]  # Show first 10
            raise SQLGenerationError(
                f"Invalid columns used in query for table '{table_key}': {', '.join(invalid_columns)}. "
                f"These columns do not exist in the selected table. "
                f"Available columns include: {', '.join(available_columns)}..."
            )
    
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

