"""
Semantic Service

This service manages the semantic layer - the business definitions of tables,
columns, measures, and derived measures.

Responsibilities:
1. Load semantic layer (with caching)
2. Reload semantic layer (refresh cache)
3. Get table information
4. Get column information
5. Validate tables and columns exist
6. Get available measures and derived measures

Flow:
Service → SemanticRepository → JSON File → SemanticLayer (domain model)
"""

from typing import Optional, List, Dict, Any

from app.core.models.semantic import SemanticLayer, Table, Column, DerivedMeasure
from app.core.exceptions import SemanticLayerError
from app.repositories.base import SemanticRepository
from app.config import get_logger

logger = get_logger(__name__)


class SemanticService:
    """
    Service for managing semantic layer.
    
    This service provides a clean interface for accessing semantic layer data.
    It handles caching and provides convenient methods for common operations.
    """
    
    def __init__(
        self,
        semantic_repository: SemanticRepository,
    ):
        """
        Initialize SemanticService with dependencies.
        
        Args:
            semantic_repository: Repository for loading semantic layer
        
        Why dependency injection?
        - Easy to test (can pass mock repository)
        - Easy to swap implementations (file → database → API)
        - Clear dependencies
        """
        self.semantic_repository = semantic_repository
        # Cache the semantic layer for performance
        self._cached_semantic: Optional[SemanticLayer] = None
    
    # ============================================================
    # FUNCTION 1: Load Semantic Layer (with caching)
    # ============================================================
    
    async def load_semantic_layer(self) -> SemanticLayer:
        """
        Load semantic layer from repository (with caching).
        
        Flow:
        SemanticService
            ↓ checks
        Is semantic layer cached?
            ↓ if YES
        Return cached semantic layer
            ↓ if NO
        Call semantic_repository.load_semantic()
            ↓ loads
        JSON File → SemanticLayer (domain model)
            ↓ caches
        Store in self._cached_semantic
            ↓ returns
        SemanticLayer
        
        Why caching?
        - Semantic layer doesn't change often
        - Loading from file is expensive (I/O operation)
        - Cache improves performance
        
        Returns:
            SemanticLayer: The semantic layer domain model
        
        Raises:
            SemanticLayerError: If semantic layer cannot be loaded
        
        Example:
            service = SemanticService(repo)
            semantic = await service.load_semantic_layer()
            table = semantic.get_table("customers")
        """
        # Check if we have cached semantic layer
        if self._cached_semantic is not None:
            logger.debug("Returning cached semantic layer")
            return self._cached_semantic
        
        # Cache is empty, load from repository
        logger.info("Loading semantic layer from repository")
        
        try:
            # Repository loads from file and converts to domain model
            semantic = await self.semantic_repository.load_semantic()
            
            # Cache it for next time
            self._cached_semantic = semantic
            
            logger.info(f"Semantic layer loaded: {len(semantic.tables)} tables")
            return semantic
            
        except Exception as e:
            logger.error(f"Failed to load semantic layer: {e}")
            raise SemanticLayerError(f"Failed to load semantic layer: {e}") from e
    
    # ============================================================
    # FUNCTION 2: Reload Semantic Layer (clear cache)
    # ============================================================
    
    async def reload_semantic_layer(self) -> SemanticLayer:
        """
        Reload semantic layer from repository (clears cache first).
        
        Flow:
        SemanticService
            ↓ clears
        self._cached_semantic = None (clear cache)
            ↓ calls
        semantic_repository.reload_semantic()
            ↓ loads
        JSON File → SemanticLayer (domain model)
            ↓ caches
        Store in self._cached_semantic
            ↓ returns
        SemanticLayer
        
        When to use this?
        - After updating semantic.json file
        - When you want fresh data (not cached)
        - During development when semantic layer changes
        
        Difference from load_semantic_layer():
        - load_semantic_layer() → Uses cache if available (fast)
        - reload_semantic_layer() → Always reloads (fresh data)
        
        Returns:
            SemanticLayer: Freshly loaded semantic layer
        
        Raises:
            SemanticLayerError: If semantic layer cannot be loaded
        
        Example:
            # After updating semantic.json
            service = SemanticService(repo)
            semantic = await service.reload_semantic_layer()
        """
        logger.info("Reloading semantic layer (clearing cache)")
        
        # Clear cache first
        self._cached_semantic = None
        
        try:
            # Repository reloads from file (clears its own cache too)
            semantic = await self.semantic_repository.reload_semantic()
            
            # Cache the fresh data
            self._cached_semantic = semantic
            
            logger.info(f"Semantic layer reloaded: {len(semantic.tables)} tables")
            return semantic
            
        except Exception as e:
            logger.error(f"Failed to reload semantic layer: {e}")
            raise SemanticLayerError(f"Failed to reload semantic layer: {e}") from e
    
    # ============================================================
    # FUNCTION 3: Get Table by Name
    # ============================================================
    
    async def get_table(self, table_name: str) -> Table:
        """
        Get a specific table from the semantic layer.
        
        Flow:
        SemanticService
            ↓ ensures
        Load semantic layer (if not cached)
            ↓ calls
        semantic.get_table(table_name)
            ↓ returns
        Table (domain model) or None
            ↓ checks
        If None → Raise SemanticLayerError
        If found → Return Table
        
        Why this function?
        - Convenience method (loads semantic layer automatically)
        - Handles errors gracefully
        - Provides clean interface
        
        Args:
            table_name: Name of the table to retrieve
        
        Returns:
            Table: The table domain model
        
        Raises:
            SemanticLayerError: If table not found or semantic layer cannot be loaded
        
        Example:
            service = SemanticService(repo)
            table = await service.get_table("customers")
            columns = table.columns  # Dict of Column objects
        """
        logger.debug(f"Getting table: {table_name}")
        
        # Ensure semantic layer is loaded (uses cache if available)
        semantic = await self.load_semantic_layer()
        
        # Get table from semantic layer
        table = semantic.get_table(table_name)
        
        if table is None:
            available_tables = semantic.get_all_table_names()
            logger.warning(f"Table '{table_name}' not found. Available: {available_tables}")
            raise SemanticLayerError(
                f"Table '{table_name}' not found in semantic layer. "
                f"Available tables: {', '.join(available_tables)}"
            )
        
        logger.debug(f"Table '{table_name}' retrieved successfully")
        return table
    
    # ============================================================
    # FUNCTION 4: Get Column from Table
    # ============================================================
    
    async def get_column(
        self,
        table_name: str,
        column_name: str,
    ) -> Column:
        """
        Get a specific column from a specific table.
        
        Flow:
        SemanticService
            ↓ gets
        Table (using get_table())
            ↓ calls
        table.get_column(column_name)
            ↓ returns
        Column (domain model) or None
            ↓ checks
        If None → Raise SemanticLayerError
        If found → Return Column
        
        Why this function?
        - Convenience method (handles table lookup automatically)
        - Validates both table and column exist
        - Provides helpful error messages
        
        Args:
            table_name: Name of the table
            column_name: Name of the column
        
        Returns:
            Column: The column domain model
        
        Raises:
            SemanticLayerError: If table or column not found
        
        Example:
            service = SemanticService(repo)
            column = await service.get_column("customers", "customer_name")
            # Now you can use:
            column_type = column.type  # "dimension", "measure", or "date"
            is_dimension = column.is_dimension()  # True/False
        """
        logger.debug(f"Getting column '{column_name}' from table '{table_name}'")
        
        # First, get the table (this validates table exists)
        table = await self.get_table(table_name)
        
        # Get column from table
        column = table.get_column(column_name)
        
        if column is None:
            available_columns = list(table.columns.keys())
            logger.warning(
                f"Column '{column_name}' not found in table '{table_name}'. "
                f"Available columns: {available_columns}"
            )
            raise SemanticLayerError(
                f"Column '{column_name}' not found in table '{table_name}'. "
                f"Available columns: {', '.join(available_columns)}"
            )
        
        logger.debug(f"Column '{column_name}' retrieved from table '{table_name}'")
        return column
    
    # ============================================================
    # FUNCTION 5: Validate Table Exists
    # ============================================================
    
    async def validate_table_exists(self, table_name: str) -> bool:
        """
        Validate that a table exists in the semantic layer.
        
        Flow:
        SemanticService
            ↓ loads
        Semantic layer (if not cached)
            ↓ checks
        semantic.has_table(table_name)
            ↓ returns
        True if exists, False otherwise
        
        Why this function?
        - Simple validation (returns bool, doesn't raise exception)
        - Useful for conditional logic
        - Fast (uses cache if available)
        
        Difference from get_table():
        - get_table() → Returns Table or raises exception
        - validate_table_exists() → Returns True/False (no exception)
        
        Args:
            table_name: Name of the table to validate
        
        Returns:
            bool: True if table exists, False otherwise
        
        Example:
            service = SemanticService(repo)
            if await service.validate_table_exists("customers"):
                # Table exists, proceed
                table = await service.get_table("customers")
            else:
                # Table doesn't exist
                print("Table not found")
        """
        logger.debug(f"Validating table exists: {table_name}")
        
        # Load semantic layer (uses cache if available)
        semantic = await self.load_semantic_layer()
        
        # Check if table exists
        exists = semantic.has_table(table_name)
        
        if exists:
            logger.debug(f"Table '{table_name}' exists")
        else:
            logger.debug(f"Table '{table_name}' does not exist")
        
        return exists
    
    # ============================================================
    # FUNCTION 6: Validate Column Exists
    # ============================================================
    
    async def validate_column_exists(
        self,
        table_name: str,
        column_name: str,
    ) -> bool:
        """
        Validate that a column exists in a specific table.
        
        Flow:
        SemanticService
            ↓ loads
        Semantic layer (if not cached)
            ↓ validates
        Table exists (using validate_table_exists)
            ↓ checks
        semantic.validate_column_exists(table_name, column_name)
            ↓ returns
        True if exists, False otherwise
        
        Why this function?
        - Simple validation (returns bool, doesn't raise exception)
        - Validates both table AND column
        - Useful for conditional logic
        
        Difference from get_column():
        - get_column() → Returns Column or raises exception
        - validate_column_exists() → Returns True/False (no exception)
        
        Args:
            table_name: Name of the table
            column_name: Name of the column to validate
        
        Returns:
            bool: True if column exists in table, False otherwise
        
        Example:
            service = SemanticService(repo)
            if await service.validate_column_exists("customers", "customer_name"):
                # Column exists, proceed
                column = await service.get_column("customers", "customer_name")
            else:
                # Column doesn't exist
                print("Column not found")
        """
        logger.debug(f"Validating column '{column_name}' exists in table '{table_name}'")
        
        # First, validate table exists
        if not await self.validate_table_exists(table_name):
            logger.debug(f"Table '{table_name}' does not exist")
            return False
        
        # Load semantic layer (uses cache if available)
        semantic = await self.load_semantic_layer()
        
        # Check if column exists in table
        exists = semantic.validate_column_exists(table_name, column_name)
        
        if exists:
            logger.debug(f"Column '{column_name}' exists in table '{table_name}'")
        else:
            logger.debug(f"Column '{column_name}' does not exist in table '{table_name}'")
        
        return exists
    
    # ============================================================
    # FUNCTION 7: Get All Table Names
    # ============================================================
    
    async def get_all_tables(self) -> List[str]:
        """
        Get a list of all table names in the semantic layer.
        
        Flow:
        SemanticService
            ↓ loads
        Semantic layer (if not cached)
            ↓ calls
        semantic.get_all_table_names()
            ↓ returns
        List[str] (list of table names)
        
        Why this function?
        - Convenience method (loads semantic layer automatically)
        - Useful for listing available tables
        - Can be used for UI dropdowns, validation, etc.
        
        Returns:
            List[str]: List of all table names in the semantic layer
        
        Example:
            service = SemanticService(repo)
            tables = await service.get_all_tables()
            # Returns: ["customers", "orders", "products", ...]
            
            # Use in UI dropdown
            for table_name in tables:
                print(f"Available table: {table_name}")
        """
        logger.debug("Getting all table names")
        
        # Load semantic layer (uses cache if available)
        semantic = await self.load_semantic_layer()
        
        # Get all table names
        table_names = semantic.get_all_table_names()
        
        logger.debug(f"Found {len(table_names)} tables: {table_names}")
        return table_names
    
    # ============================================================
    # FUNCTION 8: Get All Columns for a Table
    # ============================================================
    
    async def get_table_columns(self, table_name: str) -> Dict[str, Column]:
        """
        Get all columns for a specific table.
        
        Flow:
        SemanticService
            ↓ gets
        Table (using get_table())
            ↓ accesses
        table.columns (Dict[str, Column])
            ↓ returns
        Dict[str, Column] (column_name → Column object)
        
        Why this function?
        - Convenience method (handles table lookup automatically)
        - Returns all columns as a dictionary
        - Useful for listing columns, validation, etc.
        
        Args:
            table_name: Name of the table
        
        Returns:
            Dict[str, Column]: Dictionary mapping column names to Column objects
        
        Raises:
            SemanticLayerError: If table not found
        
        Example:
            service = SemanticService(repo)
            columns = await service.get_table_columns("customers")
            # Returns: {
            #     "customer_id": Column(...),
            #     "customer_name": Column(...),
            #     "customer_email": Column(...),
            #     ...
            # }
            
            # Iterate over columns
            for col_name, column in columns.items():
                print(f"{col_name}: {column.type}")
        """
        logger.debug(f"Getting all columns for table '{table_name}'")
        
        # Get table (this validates table exists)
        table = await self.get_table(table_name)
        
        # Return all columns
        columns = table.columns
        
        logger.debug(f"Found {len(columns)} columns in table '{table_name}'")
        return columns
    
    # ============================================================
    # FUNCTION 9: Get Measures and Derived Measures
    # ============================================================
    
    async def get_measures(
        self,
        table_name: str,
    ) -> Dict[str, Any]:
        """
        Get all measures and derived measures for a specific table.
        
        Flow:
        SemanticService
            ↓ gets
        Table (using get_table())
            ↓ accesses
        table.measures (List[str]) - regular measure column names
        table.derived_measures (List[DerivedMeasure]) - calculated measures
            ↓ combines
        Returns dictionary with both
        
        Why this function?
        - Convenience method (handles table lookup automatically)
        - Returns both regular and derived measures
        - Useful for AI prompts, UI dropdowns, etc.
        
        Args:
            table_name: Name of the table
        
        Returns:
            Dict[str, Any]: Dictionary containing:
                - "measures": List[str] - regular measure column names
                - "derived_measures": List[DerivedMeasure] - derived measure objects
        
        Raises:
            SemanticLayerError: If table not found
        
        Example:
            service = SemanticService(repo)
            measures = await service.get_measures("sales")
            # Returns: {
            #     "measures": ["sales_amount", "quantity", "discount"],
            #     "derived_measures": [
            #         DerivedMeasure(name="profit_margin", expression="...", ...),
            #         ...
            #     ]
            # }
            
            # Use regular measures
            for measure_name in measures["measures"]:
                print(f"Measure: {measure_name}")
            
            # Use derived measures
            for dm in measures["derived_measures"]:
                print(f"Derived: {dm.name} = {dm.expression}")
        """
        logger.debug(f"Getting measures for table '{table_name}'")
        
        # Get table (this validates table exists)
        table = await self.get_table(table_name)
        
        # Return both regular measures and derived measures
        result = {
            "measures": table.measures,  # List[str] - regular measure column names
            "derived_measures": table.derived_measures,  # List[DerivedMeasure] - calculated measures
        }
        
        logger.debug(
            f"Found {len(table.measures)} measures and "
            f"{len(table.derived_measures)} derived measures in table '{table_name}'"
        )
        return result
    
    # ============================================================
    # FUNCTION 10: Get Semantic Layer as Dictionary
    # ============================================================
    
    async def get_semantic_layer_dict(self) -> Dict[str, Any]:
        """
        Get the complete semantic layer as a dictionary.
        
        Flow:
        SemanticService
            ↓ loads
        Semantic layer (if not cached)
            ↓ calls
        semantic.to_dict()
            ↓ returns
        Dict[str, Any] (JSON-serializable dictionary)
        
        Why this function?
        - Converts domain model to dictionary
        - Useful for AI prompts (send semantic layer as JSON)
        - Useful for API responses (return semantic layer to frontend)
        - JSON serializable (can be converted to JSON string)
        
        Returns:
            Dict[str, Any]: Dictionary representation of semantic layer
        
        Example:
            service = SemanticService(repo)
            semantic_dict = await service.get_semantic_layer_dict()
            # Returns: {
            #     "tables": {
            #         "customers": {
            #             "description": "...",
            #             "columns": {...},
            #             "dimensions": [...],
            #             "measures": [...],
            #             ...
            #         },
            #         ...
            #     }
            # }
            
            # Use for AI prompt
            import json
            semantic_json = json.dumps(semantic_dict, indent=2)
            # Send to AI as context
        """
        logger.debug("Getting semantic layer as dictionary")
        
        # Load semantic layer (uses cache if available)
        semantic = await self.load_semantic_layer()
        
        # Convert to dictionary using domain model's to_dict() method
        semantic_dict = semantic.to_dict()
        
        logger.debug(f"Semantic layer converted to dictionary: {len(semantic_dict.get('tables', {}))} tables")
        return semantic_dict

