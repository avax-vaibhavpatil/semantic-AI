"""
Main FastAPI Application

This is the entry point for the API server.
It sets up FastAPI app, middleware, and includes all routes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.config import get_settings, get_logger
from app.api.v1 import router as v1_router
from app.api.dependencies import initialize_services, cleanup_services
from app.api.exception_handlers import (
    query_validation_error_handler,
    sql_generation_error_handler,
    sql_execution_error_handler,
    domain_exception_handler,
    validation_error_handler,
    generic_exception_handler,
)
from app.core.exceptions import (
    QueryValidationError,
    SQLGenerationError,
    SQLExecutionError,
    DomainException,
)

logger = get_logger(__name__)
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Auto Semantic BI Platform API",
    description="AI-powered natural language to SQL query platform",
    version="1.0.0",
)

# Add CORS middleware
# CRITICAL: When allow_credentials=True, cannot use "*" for origins
# Must specify exact origins or set allow_credentials=False
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"],  # Frontend origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # All HTTP methods
    allow_headers=["*"],  # All headers including X-User-Id
)

# Register global exception handlers
# CRITICAL: Centralized error handling prevents leaking internal errors
app.add_exception_handler(QueryValidationError, query_validation_error_handler)
app.add_exception_handler(SQLGenerationError, sql_generation_error_handler)
app.add_exception_handler(SQLExecutionError, sql_execution_error_handler)
app.add_exception_handler(DomainException, domain_exception_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include API routers
app.include_router(v1_router)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Health status
    """
    return {
        "status": "ok",
        "service": "Auto Semantic BI Platform",
        "version": "1.0.0"
    }


@app.on_event("startup")
async def startup_event():
    """
    Called when the application starts.
    
    CRITICAL: Initialize all services here (once, not per request).
    This prevents creating heavy objects (repositories, AI providers) on every request.
    """
    logger.info("🚀 Auto Semantic BI Platform API starting...")
    logger.info(f"   CORS origins: {settings.cors_origins}")
    
    # Initialize services at startup (singleton pattern)
    initialize_services()


@app.on_event("shutdown")
async def shutdown_event():
    """Called when the application shuts down"""
    logger.info("👋 Auto Semantic BI Platform API shutting down...")
    cleanup_services()

