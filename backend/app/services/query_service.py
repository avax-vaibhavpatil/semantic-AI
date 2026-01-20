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
from app.services.query_preprocessor import QueryPreprocessor

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
        self.preprocessor = QueryPreprocessor()  # Initialize preprocessor
    
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
            # STEP 2: Preprocess Query (Extract Entities)
            # ===================================================================
            # Extract structured entities (company, branch, make) from natural language
            # This reduces system prompt complexity and improves accuracy
            extracted_entities = self.preprocessor.extract_entities(request.question)
            logger.debug(f"Extracted entities: {extracted_entities}")
            
            # ===================================================================
            # STEP 3: Detect Table from Question
            # ===================================================================
            # Pre-detect which table the user is asking about to enforce strict selection
            detected_table = self._detect_table_from_question(request.question, semantic_layer)
            
            # ===================================================================
            # STEP 4: Build AI Prompts
            # ===================================================================
            # System prompt: Instructions for AI
            # User prompt: User's question + semantic layer context + table enforcement + extracted entities
            # Pass semantic_layer to system prompt to dynamically extract name columns
            system_prompt = self._build_system_prompt(detected_table, semantic_layer)
            user_prompt = self._build_user_prompt(
                extracted_entities.get("enhanced_question", request.question),
                semantic_layer,
                detected_table,
                extracted_entities
            )
            
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
            max_retries = 3  # Increased retries for better success rate
            retry_count = 0
            while retry_count < max_retries:
                try:
                    if detected_table:
                        self._validate_table_selection(sql, detected_table)
                        # Also validate that columns used exist in the selected table
                        self._validate_columns_exist(sql, detected_table, semantic_layer)
                        # Validate that code columns are not used with text values
                        self._validate_name_vs_code_columns(sql, detected_table, semantic_layer)
                        # Validate case-insensitive matching and NULL handling
                        self._validate_case_and_null_handling(sql, detected_table, extracted_entities)
                        # Validate that extracted entities are used correctly
                        if extracted_entities:
                            self._validate_extracted_entities(sql, detected_table, extracted_entities)
                    break  # All validations passed
                except SQLGenerationError as validation_error:
                    if retry_count < max_retries - 1:
                        # Retry with corrected instructions
                        logger.warning(f"Validation failed (attempt {retry_count + 1}/{max_retries}), retrying with corrected instructions: {validation_error}")
                        # Extract the specific correction from error message
                        error_msg = str(validation_error)
                        correction_hint = ""
                        if "Use '" in error_msg and "instead" in error_msg:
                            # Extract the suggested column from error message
                            import re
                            match = re.search(r"Use '(\w+)' instead", error_msg)
                            if match:
                                correct_col = match.group(1)
                                # Extract wrong column from error message
                                wrong_match = re.search(r"'(\w+)' is an", error_msg)
                                if wrong_match:
                                    wrong_col = wrong_match.group(1)
                                    correction_hint = f"\n\nCRITICAL FIX: Replace '{wrong_col}' with '{correct_col}' in the WHERE clause."
                        
                        # Enhanced correction hints for LOWER() and COALESCE() issues
                        enhanced_correction = correction_hint
                        if "LOWER()" in error_msg or "COALESCE()" in error_msg:
                            enhanced_correction = "\n\nCRITICAL FIXES REQUIRED:\n"
                            if "LOWER()" in error_msg:
                                enhanced_correction += "- For ALL text column comparisons (company_name, branch_name, item_name), you MUST use LOWER() function:\n"
                                enhanced_correction += "  WRONG: WHERE branch_name = 'Mumbai'\n"
                                enhanced_correction += "  CORRECT: WHERE LOWER(branch_name) = LOWER('Mumbai')\n"
                                enhanced_correction += "  WRONG: WHERE company_name LIKE '%shree nm%'\n"
                                enhanced_correction += "  CORRECT: WHERE LOWER(company_name) LIKE LOWER('%shree nm%')\n"
                            if "COALESCE()" in error_msg:
                                enhanced_correction += "- For ALL numeric comparisons with zero (sale90, stock_level), you MUST use COALESCE():\n"
                                enhanced_correction += "  WRONG: WHERE stgw_sale90 = 0\n"
                                enhanced_correction += "  CORRECT: WHERE COALESCE(stgw_sale90, 0) = 0\n"
                                enhanced_correction += "  This is critical because NULL values won't match = 0 without COALESCE()\n"
                        
                        retry_prompt = f"{user_prompt}\n\nIMPORTANT CORRECTION: The previous SQL had validation errors: {validation_error}{enhanced_correction}\n\nPlease regenerate the SQL with ALL corrections applied. Make sure to:\n1. Use LOWER() for ALL text column comparisons\n2. Use COALESCE() for ALL numeric comparisons with zero"
                        sql = await asyncio.wait_for(
                            loop.run_in_executor(
                                None,
                                lambda: self.ai_router.generate_sql(
                                    system_prompt=system_prompt,
                                    user_prompt=retry_prompt,
                                    temperature=0.0,
                                    max_tokens=1500,
                                )
                            ),
                            timeout=ai_timeout,
                        )
                        logger.info(f"SQL regenerated after validation error (attempt {retry_count + 1}): {sql[:100]}...")
                        retry_count += 1
                    else:
                        # Max retries reached, raise the error
                        logger.error(f"Validation failed after {max_retries} retries. Final SQL: {sql[:200]}")
                        raise
            
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
                "stgw_", "nos count", "quality breakdown", "items with sales", "items with profit",
                "sales value", "sale value", "profit loss", "highest profit", "items profit",
                "items with", "list of items"
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
                "budget", "customer", "customers", "handler", "salesperson", "salesman", "saleman",  # Added typo variant
                "outstanding", "outstandings", "profit loss", "profit and loss", "last 90 days sales",
                "last year sale", "last year sales", "lytd sales", "lymtd sale", "lymtd sales"  # Added last year indicators
            ]
        }
        
        scores = {}
        
        # Filter out common stop words that cause false matches
        stop_words = {'the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can', 'me', 'my', 'we', 'our', 'you', 'your', 'their', 'them', 'this', 'that', 'these', 'those', 'show', 'me', 'get', 'give', 'find', 'where', 'what', 'which', 'who', 'when', 'how', 'and', 'or', 'but', 'if', 'then', 'else'}
        meaningful_words = question_words - stop_words
        
        # Analyze each table in the semantic layer
        for table_key, table in semantic_layer.tables.items():
            score = 0
            
            # PRIORITY 1: Check explicit table name FIRST (strongest signal)                                                                                                                                                                                                                                                                                                               
            # If user explicitly mentions table name, that's definitive
            table_name_lower = table_key.lower()
            if table_key in question_lower or table_name_lower.replace("public.", "") in question_lower:                                                                                                                                        
                score += 50  # Very high weight for explicit table mention                                                                                                                                                                          
                logger.debug(f"Explicit table name match: {table_key}")
                # Early exit optimization: if explicit table name found, skip other checks for this table
                # (but still check other tables in case user mentions multiple)
            
            # PRIORITY 2: Check column aliases (semantic layer is primary source)
            # This is the most reliable way to match user intent to actual columns
            for col_name, col in table.columns.items():
                # Check column aliases with improved fuzzy matching
                for alias in col.aliases:
                    alias_lower = alias.lower()
                    alias_words = alias_lower.split()
                    
                    # Exact alias match (highest priority) - use word boundaries to avoid false matches
                    # Check if alias appears as a whole word, not as substring
                    import re
                    alias_pattern = r'\b' + re.escape(alias_lower) + r'\b'
                    if re.search(alias_pattern, question_lower):
                        score += 25  # Very high weight - semantic layer match
                        logger.debug(f"Exact alias match: '{alias}' in {table_key}")
                    
                    # Fuzzy match for typos (e.g., "saleman" -> "salesman")
                    else:
                        for alias_word in alias_words:
                            if len(alias_word) > 4:  # Only meaningful words
                                for q_word in meaningful_words:
                                    # Check if words are similar (typo tolerance)
                                    if abs(len(q_word) - len(alias_word)) <= 2:
                                        # Check substring match or similarity
                                        if alias_word in q_word or q_word in alias_word:
                                            # Additional check: if it's a known typo pattern
                                            if (alias_word.startswith('sales') and q_word.startswith('sale')) or \
                                               (alias_word.startswith('sales') and 'sale' in q_word):
                                                score += 20  # High weight for typo match
                                                logger.debug(f"Typo alias match: '{q_word}' -> '{alias_word}' in {table_key}")
                                                break
                
                # Check if column name itself appears (but lower priority than aliases)
                col_name_lower = col_name.lower()
                if col_name_lower in question_lower:
                    score += 15  # High weight for column name match
            
            # PRIORITY 3: Check measures (semantic layer)
            for measure in table.measures:
                measure_lower = str(measure).lower()
                # Check if measure name or key parts appear
                if measure_lower in question_lower:
                    score += 20  # High weight for measure match
                # Also check for partial matches (e.g., "last year sale" -> "lytd_sales")
                measure_parts = measure_lower.split('_')
                for part in measure_parts:
                    if len(part) > 3 and part in question_lower:
                        score += 12  # Partial measure match
            
            # PRIORITY 3.5: Special handling for "items with sales/profit" queries
            # These should strongly indicate stock_gw table
            if "items" in question_lower and ("sales" in question_lower or "profit" in question_lower):
                if table_key == "public.stock_gw":
                    # Check if table has both item and sales/profit columns
                    has_item_col = any("item" in col.lower() for col in table.columns.keys())
                    has_sales_col = any("sale" in col.lower() or "sales" in col.lower() for col in table.columns.keys())
                    has_profit_col = any("profit" in col.lower() for col in table.columns.keys())
                    if has_item_col and (has_sales_col or has_profit_col):
                        score += 40  # Very high weight for items + sales/profit combination
                        logger.debug(f"Items with sales/profit match: {table_key}")
            
            # PRIORITY 4: Check dimensions (semantic layer)
            for dimension in table.dimensions:
                dimension_lower = str(dimension).lower()
                if dimension_lower in question_lower:
                    score += 15  # High weight for dimension match
            
            # PRIORITY 5: Check hardcoded indicators (fallback, but still useful)
            indicators = table_indicators.get(table_key, [])
            for indicator in indicators:
                if indicator in question_lower:
                    score += 15  # Useful fallback for common phrases
            
            # PRIORITY 6: Check table description (reduced weight, require 2+ word matches)
            if table.description:
                table_desc = table.description.lower()
                desc_words = set(table_desc.split()) - stop_words
                matches = meaningful_words.intersection(desc_words)
                if len(matches) >= 2:  # Only count if 2+ words match (reduce noise)
                    score += len(matches) * 3  # Reduced weight, filtered
            
            # PRIORITY 7: Check column descriptions (lowest priority, require 2+ word matches)
            for col_name, col in table.columns.items():
                if col.description:
                    col_desc = col.description.lower()
                    col_desc_words = set(col_desc.split()) - stop_words
                    col_matches = meaningful_words.intersection(col_desc_words)
                    if len(col_matches) >= 2:  # Only count if 2+ words match (reduce noise)
                        score += len(col_matches) * 1  # Lowest weight, filtered
            
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
    
    def _build_system_prompt(self, detected_table: Optional[str] = None, semantic_layer: Optional[SemanticLayer] = None) -> str:
        """
        Build the system prompt for AI.
        
        This tells AI how to generate SQL.
        System prompt = Instructions/guidelines
        
        Args:
            detected_table: Optional table that was detected from question
            semantic_layer: Optional semantic layer to extract name columns dynamically
        """
        # Dynamically extract name columns from semantic layer if provided
        name_columns_section = ""
        if semantic_layer:
            name_columns_by_table = {}
            for table_key, table in semantic_layer.tables.items():
                name_cols = [col_name for col_name in table.columns.keys() if 'name' in col_name.lower()]
                if name_cols:
                    name_columns_by_table[table_key] = name_cols
            
            if name_columns_by_table:
                name_columns_section = "\n- Available name columns in each table (NOTE: These columns do NOT have table prefixes):\n"
                for table_key, cols in name_columns_by_table.items():
                    # Show what NOT to use (with prefixes)
                    wrong_examples = []
                    for col in cols:
                        prefix = self._get_table_prefix(table_key)
                        if prefix:
                            wrong_examples.append(f"NOT {prefix}{col}")
                    wrong_str = ", ".join(wrong_examples[:2]) if wrong_examples else ""
                    name_columns_section += f"  * {table_key}: {', '.join(cols)}"
                    if wrong_str:
                        name_columns_section += f" ({wrong_str})"
                    name_columns_section += "\n"
        
        return f"""You are a SQL generator. Your task is to convert natural language questions into SQL queries.

Rules:
- Return ONLY a single SELECT statement (no explanations, no markdown)
- Use only tables and columns from the semantic layer provided
- Ensure queries are read-only (SELECT only, no INSERT/UPDATE/DELETE)
- Use proper SQL syntax
- Add LIMIT clause if not present (unless using aggregation - see below)
- CRITICAL: Do NOT include semicolon (;) in your SQL - LIMIT should come directly after ORDER BY
- Example CORRECT: SELECT ... ORDER BY column DESC LIMIT 5
- Example WRONG: SELECT ... ORDER BY column DESC; LIMIT 5
- CRITICAL: NEVER use bind parameters ($1, $2, :param, ?) - use literal values or omit filters if values not provided
- Example WRONG: WHERE company_code = :companyCode
- Example CORRECT: WHERE company_code = '03' (use actual value) or omit the filter if value not provided

CRITICAL: WHEN TO USE AGGREGATION (SUM, AVG, COUNT):
- If user asks for "value of", "total value", "sum of", "total", "aggregate", "combined", "overall" → use SUM() aggregation
- If user asks for "average", "avg", "mean" → use AVG() aggregation
- If user asks for "count", "number of", "how many" → use COUNT() aggregation
- When using aggregation, DO NOT use LIMIT 1 - aggregation returns a single row automatically
- Example: "value of stock over 4 years" → SELECT SUM(stgw_valabv_4y) as total_value FROM ... (NO LIMIT)
- Example: "total sales" → SELECT SUM(sales) as total_sales FROM ... (NO LIMIT)
- Example: "average stock level" → SELECT AVG(stock_level) as avg_stock FROM ... (NO LIMIT)
- WRONG: SELECT stgw_valabv_4y FROM ... LIMIT 1 (returns single row, may be NULL)
- CORRECT: SELECT SUM(stgw_valabv_4y) as total_value FROM ... (returns sum of all rows)
- If user asks for a list of items → use SELECT without aggregation, with LIMIT
- If user asks for a total/sum/value → use SELECT SUM() without LIMIT

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
     - Use for: Sales data (YTD sales, last year YTD sales, last 90 days sales, last year sale)
     - Use for: Budget data, customer data, handler/salesperson data
     - Use for: Outstanding amounts, profit/loss
     - Key indicators: "sales", "sale", "budget", "customer", "handler", "salesperson", "salesman", "saleman", "last year sale", "last year sales", "gws_*" columns
     - CRITICAL: If question mentions "salesman", "salesperson", "handler", "last year sale", or any sales-related query, you MUST use gwanalytics with gws_* prefix columns
     - CRITICAL: NEVER use stgw_handled_by or stgw_* columns when query is about sales/salesman - use gws_handled_by from gwanalytics

- If user mentions "stock gateway" or "gateway" → use stock_gw
- If user mentions "planning" or "reorder" → use stock_planning_data
- If user mentions "sales", "sale", "customer", "handler", "salesperson", "salesman", "saleman", or "last year sale" → use gwanalytics
- If ambiguous, check column prefixes in semantic layer - match the prefix pattern to the table
- CRITICAL: If the question mentions "stock gateway" or "gateway", you MUST use stock_gw table
- CRITICAL: If the question mentions "planning", "reorder", "requirement", "requirement based", or "based on stock level", you MUST use stock_planning_data table  
- CRITICAL: If the question mentions "sales", "sale", "customer", "handler", "salesperson", "salesman", "saleman", or "last year sale", you MUST use gwanalytics table
- NEVER use stock_planning_data when the question asks about "stock gateway" or "gateway"
- NEVER use stock_gw when the question asks about "planning", "reorder", "requirement", or "reorder levels"
- NEVER use stock_gw when the question asks about "requirement based on stock level" - this MUST use stock_planning_data
- NEVER use stock_gw or stock_planning_data when the question asks about "sales", "sale", "customer", "handler", or "salesperson/salesman"
- CRITICAL: When using gwanalytics, use ONLY gws_* columns (e.g., gws_handled_by, gws_lytd_sales, gws_ytd_sales). NEVER use stgw_* or spd_* columns
- CRITICAL: gwanalytics table does NOT have branch_name column - if filtering by company/branch, use company_name or gws_company_code
- CRITICAL: Each table has different available columns - check semantic layer to see which name columns exist in each table
- Example: stock_planning_data has branch_name, but gwanalytics does NOT have branch_name
- Example: If querying gwanalytics and user mentions "Shree NM", use company_name (if exists) or gws_company_code, NOT branch_name

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

CRITICAL: PRIORITIZE NAME COLUMNS OVER CODE COLUMNS:
- When users ask for "names" (branch names, item names, customer names, company names, handler names), ALWAYS use the name columns, NOT code columns
{name_columns_section}- IMPORTANT: Name columns are WITHOUT table prefixes - use "branch_name" not "spd_branch_name"
- Example: User asks "show me branch names" → Use branch_name, NOT spd_branch_code, NOT spd_branch_name
- Example: User asks "list customer names" → Use cust_name, NOT gws_cust_code, NOT gws_cust_name
- Example: User asks "show item names" → Use item_name, NOT spd_item_code, NOT spd_item_name, NOT stgw_item_code, NOT stgw_item_name
- Example: User asks "handler names" → Use handled_name, NOT gws_handled_by, NOT gws_handled_name
- Example: User asks "company names" → Use company_name, NOT spd_company_code, NOT spd_company_name, NOT gws_company_code, NOT gws_company_name
- RULE: If user mentions "name" or "names" in their question, prioritize name columns over code columns
- RULE: Only use code columns (like branch_code, item_code, cust_code) when user explicitly asks for "codes" or "IDs"
- RULE: Name columns are WITHOUT prefixes - use them as-is (check semantic layer for exact column names)
- When both name and code columns exist, prefer name columns for human-readable output
- Check the semantic layer JSON provided to see which name columns exist in each table

CRITICAL: USE NAME COLUMNS FOR TEXT FILTERS (MOST IMPORTANT FOR WHERE CLAUSES):
- When filtering by text values (names, not numeric codes), ALWAYS use name columns, NOT code columns
- CRITICAL: Use LOWER() function for case-insensitive matching on text columns (company_name, branch_name, item_name, etc.)
- Database values may have different cases (e.g., "Mumbai" vs "mumbai"), so always use LOWER() for text comparisons
- If the filter value contains text/spaces (like "Shree NM Bangalore", "Delton", "Mumbai", "Shree NM"), it's a NAME → use name column
- If the filter value is purely numeric (like "06", "51488", "123"), it's a CODE → use code column
- Example WRONG: WHERE spd_branch_code = 'Shree NM Bangalore' (spd_branch_code is INTEGER, can't match text - causes error)
- Example WRONG: WHERE branch_name = 'Mumbai' (case-sensitive, may not match "Mumbai" in database)
- Example CORRECT: WHERE LOWER(branch_name) = LOWER('Mumbai') (case-insensitive, matches "Mumbai" or "mumbai")
- Example WRONG: WHERE company_name LIKE '%shree nm%' (case-sensitive, may not match "Shree NM Electricals Ltd")
- Example CORRECT: WHERE LOWER(company_name) LIKE LOWER('%shree nm%') (case-insensitive, matches any case)
- Example WRONG: WHERE spd_company_code = 'Delton' (spd_company_code is INTEGER, can't match text - causes error)
- Example CORRECT: WHERE LOWER(company_name) = LOWER('Delton') (company_name is VARCHAR, case-insensitive matching)
- Example CORRECT: WHERE spd_branch_code = 06 (numeric code, use code column)
- Example CORRECT: WHERE gws_handled_by = '51488' (VARCHAR code column, use quotes for text)
- RULE: If filter value looks like a name (text with spaces, letters, not just digits) → use name column with LOWER()
- RULE: If filter value is purely numeric → use code column (but check if code column is VARCHAR or INTEGER)
- RULE: Check semantic layer to see if name column exists - if it does and value is text, use name column with LOWER()
- RULE: When user says "in [Company Name]" or "in [Branch Name]" or "[Location Name] branch" → use name column with LOWER(), NOT code column
- RULE: Common patterns that require name columns with LOWER(): "in Shree NM", "in Delton", "Mumbai branch", "Bangalore branch", "Shree NM Bangalore"
- RULE: For compound location names like "Shree NM Mumbai branch" or "in Shree NM Mumbai":
  * If the question contains EXTRACTED ENTITIES hints, use them as separate filters
  * Example: If extracted entities show "Company: Shree NM" and "Branch: Mumbai" → use company_name LIKE '%Shree NM%' AND branch_name = 'Mumbai'
  * If no entities extracted, check if location part matches a known city (Mumbai, Bangalore, Chennai, etc.)
  * If location is a known city → split into company_name and branch_name filters
  * If location is NOT a known city (e.g., "Electricals", "Ltd") → treat entire phrase as company_name
- Example: "Shree NM Mumbai branch" → company_name LIKE '%Shree NM%' AND branch_name = 'Mumbai'
- Example: "Shree NM Electricals Ltd" → company_name LIKE '%Shree NM Electricals Ltd%' (no branch filter)
- RULE: For category filters, extract ONLY the category value, NOT the word "category"
- Example: User says "Z category" → Use WHERE spd_ica_category = 'Z' (NOT 'Z category')
- Example: User says "category Z" → Use WHERE spd_ica_category = 'Z' (NOT 'category Z')
- Example: User says "A category items" → Use WHERE spd_ica_category = 'A' (NOT 'A category')
- RULE: When filtering by category, remove the word "category" from the filter value - use only the letter/number
- This is CRITICAL for WHERE clauses - wrong column type causes "invalid input syntax for type integer" errors
- ALWAYS check: Does the filter value contain letters/spaces? → Use name column. Is it purely numeric? → Use code column

CRITICAL: TYPE CASTING FOR FILTERS:
- When filtering by numeric codes (like handler codes, customer codes), check the semantic layer for column type
- If the semantic layer shows the column is VARCHAR/TEXT but you're filtering with a number, cast the number to text
- Example: If gws_handled_by is VARCHAR and user provides code 51488, use: WHERE gws_handled_by = '51488' (with quotes)
- Example: If column type is INTEGER but value is provided as text, cast: WHERE column = CAST('value' AS INTEGER)
- Always match the filter value type to the column type in the database
- Check semantic layer column descriptions for type hints (e.g., "numeric code", "integer", "varchar")

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

CRITICAL: COALESCE IN WHERE CLAUSES - NULL HANDLING:
- When filtering on numeric columns that might be NULL, ALWAYS use COALESCE in WHERE clauses
- If user asks for "zero", "is zero", "equals zero", "is null or zero", "no sales", "no stock", treat NULL as 0 using COALESCE
- Example: User says "stock level is zero" → Use: WHERE COALESCE(stock_level, 0) = 0
- Example: User says "pending stock is greater than 0" → Use: WHERE COALESCE(pending_stock, 0) > 0
- Example: User says "no stock" or "zero stock" → Use: WHERE COALESCE(stock_level, 0) = 0
- Example: User says "no sales in last 90 days" → Use: WHERE COALESCE(sale90, 0) = 0 (NOT sale90 = 0)
- Example: User says "items with no sales" → Use: WHERE COALESCE(sale_value, 0) = 0
- WRONG: WHERE stock_level = 0 (excludes NULL rows - they won't match = 0)
- CORRECT: WHERE COALESCE(stock_level, 0) = 0 (includes NULL rows as 0)
- WRONG: WHERE sale90 = 0 (excludes NULL rows - they won't match = 0, missing 1535 NULL rows)
- CORRECT: WHERE COALESCE(sale90, 0) = 0 (includes NULL rows as 0)
- WRONG: WHERE pending_stock > 0 (excludes NULL rows)
- CORRECT: WHERE COALESCE(pending_stock, 0) > 0 (includes NULL rows as 0, but > 0 excludes them)
- When comparing with zero (0), NULL values don't match, so use COALESCE to treat NULL as 0
- When comparing with > 0 or < 0, use COALESCE to ensure NULL is treated as 0 (so > 0 excludes NULL, < 0 excludes NULL)
- Key phrases that require COALESCE: "is zero", "equals zero", "is null or zero", "no stock", "zero stock", "empty stock", "no sales", "zero sales", "no sales in last 90 days", "items with no sales", "no sales", "zero sales", "no sales in last 90 days"

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
        extracted_entities: Optional[Dict[str, any]] = None,
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
        
        # Add extracted entities hints if available (table-aware)
        entity_hints = ""
        if extracted_entities:
            hints = []
            table = semantic_layer.get_table(detected_table) if detected_table else None
            
            # Company name - available in all tables
            if extracted_entities.get("company_name"):
                if table and table.has_column("company_name"):
                    # Use LOWER() for case-insensitive matching
                    hints.append(f"Company: {extracted_entities['company_name']} (use LOWER(company_name) LIKE LOWER('%{extracted_entities['company_name']}%') for case-insensitive matching)")
                elif detected_table == "public.gwanalytics":
                    # gwanalytics doesn't have company_name, use gws_company_code or company_name if it exists
                    hints.append(f"Company: {extracted_entities['company_name']} (use company_name if exists, or gws_company_code with appropriate filter)")
            
            # Branch name - NOT available in gwanalytics
            if extracted_entities.get("branch_name"):
                if table and table.has_column("branch_name"):
                    # Use LOWER() for case-insensitive matching
                    hints.append(f"Branch: {extracted_entities['branch_name']} (use LOWER(branch_name) = LOWER('{extracted_entities['branch_name']}') for case-insensitive matching)")
                elif detected_table == "public.gwanalytics":
                    # gwanalytics doesn't have branch_name - skip this hint
                    logger.warning(f"Branch '{extracted_entities['branch_name']}' extracted but gwanalytics table doesn't have branch_name column")
                else:
                    # Table not detected yet, but branch was extracted - provide generic hint
                    hints.append(f"Branch: {extracted_entities['branch_name']} (use LOWER(branch_name) = LOWER('{extracted_entities['branch_name']}') if table has branch_name column)")
            
            # Make/Brand - only available in stock_gw and stock_planning_data
            if extracted_entities.get("make"):
                if detected_table == "public.stock_gw":
                    hints.append(f"Make/Brand: {extracted_entities['make']} (use stgw_make = '{extracted_entities['make']}')")
                elif detected_table == "public.stock_planning_data":
                    hints.append(f"Make/Brand: {extracted_entities['make']} (use spd_make = '{extracted_entities['make']}')")
                elif detected_table == "public.gwanalytics":
                    # gwanalytics doesn't have make column - skip this hint
                    logger.warning(f"Make '{extracted_entities['make']}' extracted but gwanalytics table doesn't have make column")
                else:
                    # Table not detected yet, but make was extracted - provide generic hint
                    hints.append(f"Make/Brand: {extracted_entities['make']} (use make column if table has it - stgw_make for stock_gw, spd_make for stock_planning_data)")
            
            if hints:
                entity_hints = f"""

EXTRACTED ENTITIES (USE THESE IN YOUR SQL - ONLY IF TABLE HAS THESE COLUMNS):
{chr(10).join(f"- {hint}" for hint in hints)}
- When both company and branch are extracted, use BOTH filters with LOWER() for case-insensitive matching
- CRITICAL: ALWAYS use LOWER() function for text column comparisons (company_name, branch_name) to handle case differences
- CRITICAL: ALWAYS use COALESCE() for numeric comparisons with zero (sale90, stock_level, etc.) to include NULL values
- Example: LOWER(company_name) LIKE LOWER('%[company]%') AND LOWER(branch_name) = LOWER('[branch]')
- Example: COALESCE(sale90, 0) = 0 (NOT sale90 = 0)
- Do NOT combine them into a single branch_name filter
- IMPORTANT: Only use these filters if the selected table has the corresponding columns (check semantic layer above)
"""
        
        return f"""Semantic Layer:
{semantic_json}

User Question: {question}
{table_enforcement}{entity_hints}
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
    
    def _validate_name_vs_code_columns(self, sql: str, table_key: str, semantic_layer: SemanticLayer) -> None:
        """
        Validate that code columns (INTEGER) are not used with text values.
        If a text value is used, it should use the name column instead.
        Also validates that name columns used actually exist in the table.
        
        Raises:
            SQLGenerationError: If code column is used with text value or name column doesn't exist
        """
        import re
        table = semantic_layer.get_table(table_key)
        if not table:
            return
        
        # First check: Validate that name columns used actually exist in the table
        # gwanalytics doesn't have branch_name, so catch that
        name_columns_to_check = ['branch_name', 'company_name', 'item_name', 'cust_name', 'handled_name']
        for name_col in name_columns_to_check:
            # Check if this name column is used in SQL
            pattern = rf'\b{re.escape(name_col)}\b'
            if re.search(pattern, sql, re.IGNORECASE):
                # Check if it exists in the table
                if not table.has_column(name_col):
                    # Suggest alternative based on table
                    if table_key == "public.gwanalytics" and name_col == "branch_name":
                        raise SQLGenerationError(
                            f"Column '{name_col}' does not exist in table '{table_key}'. "
                            f"For company/branch filtering in gwanalytics, use 'company_name' (if exists) or 'gws_company_code' instead."
                        )
                    else:
                        raise SQLGenerationError(
                            f"Column '{name_col}' does not exist in table '{table_key}'. "
                            f"Check the semantic layer for available columns in this table."
                        )
        
        # Second check: Code columns that are INTEGER and should not be used with text values
        code_columns = {
            'spd_branch_code': 'branch_name',
            'spd_company_code': 'company_name',
            'spd_item_code': 'item_name',
            'gws_company_code': 'company_name',
            'gws_cust_code': 'cust_name',
            'stgw_branch_code': 'branch_name',
            'stgw_company_code': 'company_name',
            'stgw_item_code': 'item_name',
        }
        
        # Pattern to find WHERE clauses with code columns and text values
        # Matches: column = 'text value' or column = "text value"
        for code_col, name_col in code_columns.items():
            # Check if this code column exists in the table
            if not table.has_column(code_col):
                continue
            
            # Check if name column exists (if not, skip this check)
            if not table.has_column(name_col):
                continue
            
            # Pattern: code_column = 'text' or code_column = "text"
            # Look for code column followed by = and a quoted string
            pattern = rf'\b{re.escape(code_col)}\s*=\s*[\'"]([^\'"]+)[\'"]'
            matches = re.finditer(pattern, sql, re.IGNORECASE)
            
            for match in matches:
                value = match.group(1)
                # If value contains letters/spaces (not just digits), it's a name
                if re.search(r'[a-zA-Z\s]', value):
                    raise SQLGenerationError(
                        f"Type mismatch: '{code_col}' is an INTEGER column but was used with text value '{value}'. "
                        f"Use '{name_col}' instead for text values. "
                        f"Example: WHERE {name_col} = '{value}' instead of WHERE {code_col} = '{value}'"
                    )
    
    def _validate_case_and_null_handling(self, sql: str, table_key: str, extracted_entities: Optional[Dict[str, any]]) -> None:
        """
        Validate that text columns use LOWER() for case-insensitive matching
        and numeric comparisons with zero use COALESCE() for NULL handling.
        
        Raises:
            SQLGenerationError: If LOWER() or COALESCE() are missing where needed
        """
        import re
        sql_lower = sql.lower()
        issues = []
        
        # Check for text column comparisons without LOWER()
        text_columns = ['company_name', 'branch_name', 'item_name', 'cust_name', 'handled_name']
        for col in text_columns:
            # Pattern: column = 'value' or column LIKE '%value%' without LOWER()
            # But exclude if LOWER() is already used
            pattern_without_lower = rf'\b{re.escape(col)}\s*(?:=|like)\s*[\'"]([^\'"]+)[\'"]'
            if re.search(pattern_without_lower, sql, re.IGNORECASE):
                # Check if LOWER() is used
                if f'lower({col})' not in sql_lower:
                    issues.append(f"Column '{col}' is used without LOWER() function. Use LOWER({col}) for case-insensitive matching.")
        
        # Check for numeric comparisons with zero without COALESCE (for sale90, stock_level, etc.)
        # Only check if extracted entities suggest "no sales" or similar
        if extracted_entities:
            # Check for sale90, sale_90, or similar columns
            sale_pattern = r'\b(stgw_sale90|sale90|sale_90)\s*=\s*0\b'
            if re.search(sale_pattern, sql, re.IGNORECASE):
                # Check if COALESCE is used
                if 'coalesce' not in sql_lower or 'coalesce(stgw_sale90' not in sql_lower:
                    issues.append("Column 'stgw_sale90' is compared with 0 without COALESCE(). Use COALESCE(stgw_sale90, 0) = 0 to include NULL values.")
        
        if issues:
            raise SQLGenerationError(
                "SQL generation issues detected:\n" + "\n".join(f"- {issue}" for issue in issues) +
                "\n\nCRITICAL FIXES REQUIRED:\n" +
                "- For text columns (company_name, branch_name), ALWAYS use LOWER() function: LOWER(column) = LOWER('value')\n" +
                "- For numeric comparisons with zero (sale90, stock_level), ALWAYS use COALESCE(): COALESCE(column, 0) = 0"
            )
    
    def _validate_extracted_entities(self, sql: str, table_key: str, extracted_entities: Dict[str, any]) -> None:
        """
        Validate that extracted entities (company, branch, make) are used correctly in SQL.
        
        This is a warning-only validation - we log warnings but don't raise errors
        because the AI might have valid reasons to omit certain filters.
        
        Args:
            sql: Generated SQL query
            table_key: Selected table
            extracted_entities: Entities extracted by preprocessor
        """
        import re
        sql_lower = sql.lower()
        
        # Check if company_name was extracted but not used
        if extracted_entities.get("company_name"):
            company = extracted_entities["company_name"]
            # Check if company filter is present (either company_name or company code)
            company_pattern = r'(company_name|gws_company_code|spd_company_code|stgw_company_code)'
            if not re.search(company_pattern, sql_lower):
                logger.warning(f"Company '{company}' was extracted but not used in SQL")
        
        # Check if branch_name was extracted but not used
        if extracted_entities.get("branch_name"):
            branch = extracted_entities["branch_name"]
            # Check if branch filter is present
            branch_pattern = r'(branch_name|gws_branch_code|spd_branch_code|stgw_branch_code)'
            if not re.search(branch_pattern, sql_lower):
                logger.warning(f"Branch '{branch}' was extracted but not used in SQL")
        
        # Check if make was extracted but not used (for stock_gw table)
        if extracted_entities.get("make") and table_key == "public.stock_gw":
            make = extracted_entities["make"]
            # Check if make filter is present
            if "stgw_make" not in sql_lower:
                logger.warning(f"Make '{make}' was extracted but not used in SQL")
    
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

