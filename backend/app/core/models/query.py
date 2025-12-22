"""
Query Domain Model

Represents a user query and its execution result.
This is a pure domain model - no framework dependencies.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class QueryRequest:
    """
    Represents a user's query request
    
    This is the input - what the user wants to know.
    """
    question: str
    max_rows: int = 500
    dialect: Optional[str] = None
    
    def __post_init__(self):
        """Validate after initialization"""
        if not self.question or not self.question.strip():
            raise ValueError("Question cannot be empty")
        if self.max_rows < 1:
            raise ValueError("max_rows must be at least 1")
        if self.max_rows > 10000:
            raise ValueError("max_rows cannot exceed 10000")


@dataclass
class Query:
    """
    Represents a query with generated SQL
    
    This is the domain entity after AI processing.
    """
    question: str
    sql: str
    generated_at: datetime
    execution_time_ms: Optional[float] = None
    
    def __post_init__(self):
        """Validate after initialization"""
        if not self.question or not self.question.strip():
            raise ValueError("Question cannot be empty")
        if not self.sql or not self.sql.strip():
            raise ValueError("SQL cannot be empty")


@dataclass
class QueryResult:
    """
    Represents the result of executing a query
    
    Contains the data returned from the database.
    """
    query: Query
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: float
    executed_at: datetime
    warning: Optional[str] = None
    
    def __post_init__(self):
        """Validate after initialization"""
        if self.row_count != len(self.rows):
            raise ValueError(f"row_count ({self.row_count}) doesn't match rows length ({len(self.rows)})")
    
    @property
    def is_empty(self) -> bool:
        """Check if result is empty"""
        return self.row_count == 0
    
    @property
    def has_warning(self) -> bool:
        """Check if result has warnings"""
        return self.warning is not None

