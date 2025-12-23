"""
Async Database Connection

Creates and manages async database connections using SQLAlchemy async core.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker
from typing import Optional
from app.config import get_settings
from urllib.parse import urlparse, urlunparse


# Global variables (Singleton pattern)
_async_engine: Optional[AsyncEngine] = None
_async_session_factory: Optional[async_sessionmaker] = None


def convert_to_async_url(database_url: str) -> str:
    """
    Convert synchronous database URL to async-compatible URL
    
    PostgreSQL:
        postgresql://... → postgresql+asyncpg://...
    
    MySQL:
        mysql://... → mysql+aiomysql://...
    
    SQLite:
        sqlite:///... → sqlite+aiosqlite://...
    """
    parsed = urlparse(database_url)
    
    # Determine async driver based on scheme
    if parsed.scheme.startswith("postgresql"):
        # Replace postgresql:// with postgresql+asyncpg://
        async_scheme = "postgresql+asyncpg"
    elif parsed.scheme.startswith("mysql"):
        async_scheme = "mysql+aiomysql"
    elif parsed.scheme.startswith("sqlite"):
        async_scheme = "sqlite+aiosqlite"
    else:
        # Default: assume PostgreSQL
        async_scheme = "postgresql+asyncpg"
    
    # Reconstruct URL with async driver
    async_url = urlunparse((
        async_scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        parsed.query,
        parsed.fragment
    ))
    
    return async_url


def get_async_engine() -> AsyncEngine:
    """
    Get async SQLAlchemy engine (Singleton pattern)
    
    Creates async engine once and reuses it.
    Async engine allows non-blocking database operations.
    
    Returns:
        AsyncEngine: Async database engine
        
    Raises:
        ValueError: If DATABASE_URL is not configured
    """
    global _async_engine
    
    if _async_engine is None:
        settings = get_settings()
        
        if not settings.database_url:
            raise ValueError(
                "DATABASE_URL is required but not set. "
                "Please set it in your .env file or environment variables."
            )
        
        # Convert to async-compatible URL
        async_url = convert_to_async_url(settings.database_url)
        
        # Create async engine with connection pooling
        _async_engine = create_async_engine(
            async_url,
            # Connection pool settings
            pool_pre_ping=True,      # Check connection before using
            pool_size=20,            # Keep 20 connections ready (async can handle more)
            max_overflow=40,         # Can create 40 more if needed
            pool_recycle=3600,       # Recycle connections after 1 hour
            echo=settings.debug,     # Log SQL in debug mode
            # Async-specific settings
            future=True              # Use SQLAlchemy 2.0 style
        )
    
    return _async_engine


def get_async_session() -> async_sessionmaker:
    """
    Get async session factory
    
    Creates factory for async database sessions.
    Each request should get its own session.
    
    Returns:
        async_sessionmaker: Factory for creating async sessions
    """
    global _async_session_factory
    
    if _async_session_factory is None:
        engine = get_async_engine()
        _async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Don't expire objects after commit
            autocommit=False,        # We control transactions
            autoflush=False          # We control when to flush
        )
    
    return _async_session_factory


from typing import AsyncGenerator


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session (for FastAPI dependency injection)
    
    This is a generator that yields a session and cleans up after.
    
    Usage in FastAPI:
        @app.get("/endpoint")
        async def my_endpoint(db: AsyncSession = Depends(get_db_session)):
            # Use db here
            result = await db.execute(text("SELECT 1"))
            pass
    
    Yields:
        AsyncSession: Async database session
    """
    session_factory = get_async_session()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

