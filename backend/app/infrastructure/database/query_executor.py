"""
Async Query Executor

Executes raw SQL queries asynchronously.
This is the core of our database access layer.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from typing import List, Dict, Any, Optional
from app.infrastructure.database.connection import get_async_engine
from app.core.constants import MAX_QUERY_ROWS, DEFAULT_MAX_ROWS


async def execute_query(
    sql: str,
    engine: Optional[AsyncEngine] = None,
    max_rows: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Execute a raw SQL SELECT query asynchronously
    
    This is the main function for executing queries.
    It's async, so it doesn't block the event loop.
    
    Args:
        sql: SQL SELECT query to execute
        engine: Optional async engine (uses default if not provided)
        max_rows: Optional max rows limit (applied if query has no LIMIT)
    
    Returns:
        List[Dict[str, Any]]: Query results as list of dictionaries
    
    Raises:
        ValueError: If SQL is empty or invalid
        Exception: Database errors are propagated
    """
    if not sql or not sql.strip():
        raise ValueError("SQL query cannot be empty")
    
    # Use provided engine or get default
    if engine is None:
        engine = get_async_engine()
    
    # Add LIMIT if not present and max_rows specified
    safe_sql = sql.strip()
    if max_rows and "limit" not in safe_sql.lower():
        safe_sql = f"{safe_sql} LIMIT {max_rows}"
    
    # Execute query asynchronously
    rows: List[Dict[str, Any]] = []
    async with engine.connect() as conn:
        result = await conn.stream(text(safe_sql))
        # Convert rows to dictionaries
        async for row in result:
            rows.append(dict(row._mapping))
    return rows


async def stream_query(
    sql: str,
    engine: Optional[AsyncEngine] = None,
    max_rows: Optional[int] = None
):
    """
    Stream a raw SQL SELECT query asynchronously (row-by-row).

    Use this when you want to iterate results without loading all rows into memory.
    """
    if not sql or not sql.strip():
        raise ValueError("SQL query cannot be empty")

    if engine is None:
        engine = get_async_engine()

    safe_sql = sql.strip()
    if max_rows and "limit" not in safe_sql.lower():
        safe_sql = f"{safe_sql} LIMIT {max_rows}"

    async with engine.connect() as conn:
        result = await conn.stream(text(safe_sql))
        async for row in result:
            yield dict(row._mapping)


async def execute_query_with_limit(
    sql: str,
    max_rows: int = DEFAULT_MAX_ROWS,
    engine: Optional[AsyncEngine] = None
) -> List[Dict[str, Any]]:
    """
    Execute query with automatic row limit
    
    Convenience function that ensures queries don't return too many rows.
    
    Args:
        sql: SQL SELECT query
        max_rows: Maximum rows to return (default from constants)
        engine: Optional async engine
    
    Returns:
        List[Dict[str, Any]]: Query results
    """
    # Validate max_rows
    if max_rows < 1:
        max_rows = DEFAULT_MAX_ROWS
    if max_rows > MAX_QUERY_ROWS:
        max_rows = MAX_QUERY_ROWS
    
    return await execute_query(sql, engine=engine, max_rows=max_rows)


async def execute_query_with_session(
    sql: str,
    session: AsyncSession,
    max_rows: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Execute query using an existing async session
    
    Useful when you need to execute multiple queries in a transaction.
    
    Args:
        sql: SQL SELECT query
        session: Existing async session
        max_rows: Optional max rows limit
    
    Returns:
        List[Dict[str, Any]]: Query results
    """
    if not sql or not sql.strip():
        raise ValueError("SQL query cannot be empty")
    
    safe_sql = sql.strip()
    if max_rows and "limit" not in safe_sql.lower():
        safe_sql = f"{safe_sql} LIMIT {max_rows}"
    
    result = await session.execute(text(safe_sql))
    rows = [dict(row._mapping) for row in result]
    
    return rows

