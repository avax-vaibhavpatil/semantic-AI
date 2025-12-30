"""
Global Exception Handlers

Centralized exception handling for all routes.
Converts domain exceptions to HTTP responses with secure error messages.

CRITICAL: Prevents leaking internal exception details to API clients.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.exceptions import (
    QueryValidationError,
    SQLGenerationError,
    SQLExecutionError,
    DomainException,
)
from app.config import get_logger

logger = get_logger(__name__)


async def query_validation_error_handler(
    request: Request,
    exc: QueryValidationError,
) -> JSONResponse:
    """
    Handle QueryValidationError → HTTP 400.
    
    CRITICAL: Returns user-friendly error message, logs full details internally.
    """
    logger.warning(f"Query validation error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Invalid query request",
            "detail": str(exc),  # User-friendly message from domain exception
        },
    )


async def sql_generation_error_handler(
    request: Request,
    exc: SQLGenerationError,
) -> JSONResponse:
    """
    Handle SQLGenerationError → HTTP 500.
    
    CRITICAL: Returns generic error message, logs full details internally.
    Prevents leaking internal AI provider errors to clients.
    """
    logger.error(f"SQL generation error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Failed to generate SQL query",
            "detail": "Unable to process your query. Please try again or rephrase your question.",
        },
    )


async def sql_execution_error_handler(
    request: Request,
    exc: SQLExecutionError,
) -> JSONResponse:
    """
    Handle SQLExecutionError → HTTP 500.
    
    CRITICAL: Returns generic error message, logs full details internally.
    Prevents leaking database errors to clients.
    """
    logger.error(f"SQL execution error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Failed to execute query",
            "detail": "An error occurred while executing your query. Please try again.",
        },
    )


async def domain_exception_handler(
    request: Request,
    exc: DomainException,
) -> JSONResponse:
    """
    Handle generic DomainException → HTTP 500.
    
    CRITICAL: Catches any unhandled domain exceptions.
    """
    logger.error(f"Domain exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "An error occurred",
            "detail": "An unexpected error occurred. Please try again.",
        },
    )


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle Pydantic validation errors → HTTP 422.
    
    CRITICAL: Returns validation errors in standard format.
    """
    logger.warning(f"Request validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "detail": exc.errors(),
        },
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle unexpected exceptions → HTTP 500.
    
    CRITICAL: Catches all unexpected errors, logs full details, returns generic message.
    Prevents leaking internal errors to clients.
    """
    logger.exception(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later.",
        },
    )

