"""
Database Configuration Module

This module handles database connection setup and configuration.
It provides:
1. SQLAlchemy engine creation with connection pooling
2. Session management
3. Database connection utilities

Key Concepts:
- Connection Pooling: Reuses database connections (faster, efficient)
- pool_pre_ping: Checks if connection is alive before using
- Session Management: Properly handles database transactions
"""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, Optional
from app.config import get_settings

# Global variables to store engine and session factory
# These are created once and reused (Singleton pattern)
_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def get_database_engine() -> Engine:
    """
    Get SQLAlchemy database engine (Singleton pattern)
    
    Creates the engine once and reuses it for all database connections.
    This is efficient because:
    - Connection pooling is configured once
    - Engine creation is expensive, so we do it once
    
    Returns:
        Engine: SQLAlchemy engine instance
        
    Raises:
        ValueError: If DATABASE_URL is not configured
    """
    global _engine
    
    if _engine is None:
        settings = get_settings()
        
        if not settings.database_url:
            raise ValueError(
                "DATABASE_URL is required but not set. "
                "Please set it in your .env file or environment variables."
            )
        
        # Create engine with connection pooling
        _engine = create_engine(
            settings.database_url,
            # Connection pool settings
            pool_pre_ping=True,  # Check if connection is alive before using
            pool_size=5,         # Number of connections to keep in pool
            max_overflow=10,     # Additional connections if pool is full
            pool_recycle=3600,   # Recycle connections after 1 hour
            echo=settings.debug  # Log SQL queries in debug mode
        )
    
    return _engine


def get_session_factory() -> sessionmaker:
    """
    Get database session factory
    
    Session factory creates new database sessions.
    Each request should get its own session.
    
    Returns:
        sessionmaker: Factory for creating database sessions
    """
    global _SessionLocal
    
    if _SessionLocal is None:
        engine = get_database_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,  # Don't auto-commit (we control transactions)
            autoflush=False,   # Don't auto-flush (we control when to save)
            bind=engine        # Use our engine
        )
    
    return _SessionLocal


def get_db_session() -> Generator[Session, None, None]:
    """
    Get database session (Dependency for FastAPI)
    
    This is a generator function that:
    1. Creates a new database session
    2. Yields it for use
    3. Closes the session when done (even if error occurs)
    
    Usage in FastAPI:
        @app.get("/endpoint")
        def my_endpoint(db: Session = Depends(get_db_session)):
            # Use db here
            pass
    
    Yields:
        Session: Database session
    """
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        yield session
        session.commit()  # Commit if no errors
    except Exception:
        session.rollback()  # Rollback on error
        raise
    finally:
        session.close()  # Always close session


def test_database_connection() -> bool:
    """
    Test database connection
    
    Tries to connect to the database and execute a simple query.
    Useful for health checks and startup validation.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        engine = get_database_engine()
        from sqlalchemy import text
        with engine.connect() as conn:
            # Execute simple query to test connection
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


# ============================================================================
# Explanation of Connection Pooling
# ============================================================================

"""
What is Connection Pooling?

Instead of creating a new database connection for every query (slow),
we create a "pool" of connections and reuse them.

Example:
- Without pooling: Each query = new connection (100ms overhead each time)
- With pooling: Reuse existing connections (0ms overhead)

Pool Settings Explained:
- pool_size=5: Keep 5 connections ready
- max_overflow=10: If all 5 are busy, create up to 10 more
- pool_recycle=3600: Close and recreate connections after 1 hour
- pool_pre_ping=True: Check if connection is alive before using

Why pool_pre_ping?
Sometimes database connections die (network issues, timeout).
pool_pre_ping checks if connection is alive before using it.
If dead, it creates a new one automatically.
"""

