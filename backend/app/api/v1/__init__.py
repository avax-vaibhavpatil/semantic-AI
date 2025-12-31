"""
API v1 Routes

This module contains all API endpoints for version 1.
"""

from fastapi import APIRouter

# Create API router
router = APIRouter(prefix="/api/v1", tags=["v1"])

# Import routes
from .routes.query import router as query_router
from .routes.reports import router as reports_router
router.include_router(query_router)
router.include_router(reports_router)

__all__ = ["router"]

