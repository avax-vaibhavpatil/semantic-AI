"""
Dependency Container

Centralized service initialization at app startup.
Services are created ONCE and reused across requests (singleton pattern).

CRITICAL: Prevents creating heavy objects (repositories, AI providers) on every request.
"""

from typing import Optional
from app.services.query_service import QueryService
from app.services.report_service import ReportService
from app.repositories.semantic_repository import MultiFileSemanticRepository
from app.repositories.report_repository import AsyncReportRepository
from app.infrastructure.ai.router import ProviderRouter
from app.infrastructure.ai.providers.claude_provider import ClaudeProvider
from app.infrastructure.ai.providers.groq_provider import GroqProvider
from app.config import get_logger

logger = get_logger(__name__)

# Singleton instances (created at startup, reused for all requests)
_query_service: Optional[QueryService] = None
_report_service: Optional[ReportService] = None


def initialize_services() -> None:
    """
    Initialize all services at app startup.
    
    CRITICAL: Called once during app startup, not per request.
    This prevents creating heavy objects (repositories, AI providers) on every request.
    """
    global _query_service, _report_service
    
    if _query_service is not None or _report_service is not None:
        logger.warning("Services already initialized, skipping")
        return
    
    logger.info("Initializing services at startup...")
    
    # Initialize repositories (lightweight, can be reused)
    # Use MultiFileSemanticRepository to load all JSON files from metadata/
    semantic_repo = MultiFileSemanticRepository()
    logger.debug("MultiFileSemanticRepository initialized")
    
    report_repo = AsyncReportRepository()
    logger.debug("ReportRepository initialized")
    
    # Initialize AI providers (heavy objects - created once)
    claude_provider = ClaudeProvider()
    groq_provider = GroqProvider()
    logger.debug(f"AI providers initialized: Claude={claude_provider.is_configured()}, Groq={groq_provider.is_configured()}")
    
    # Initialize router with providers
    providers = [claude_provider, groq_provider]
    ai_router = ProviderRouter(providers)
    logger.debug("ProviderRouter initialized")
    
    # Create QueryService (singleton - reused for all requests)
    _query_service = QueryService(
        semantic_repository=semantic_repo,
        ai_router=ai_router,
    )
    logger.debug("QueryService initialized")
    
    # Create ReportService (singleton - reused for all requests)
    _report_service = ReportService(
        report_repository=report_repo,
    )
    logger.debug("ReportService initialized")
    
    logger.info("✅ All services initialized successfully")


def get_query_service() -> QueryService:
    """
    Get QueryService instance (singleton).
    
    CRITICAL: Returns pre-initialized service, does NOT create new instances.
    This ensures QueryService is created ONCE and reused.
    
    Raises:
        RuntimeError: If services not initialized (should not happen in production)
    """
    if _query_service is None:
        raise RuntimeError("Services not initialized. Call initialize_services() at app startup.")
    return _query_service


def get_report_service() -> ReportService:
    """
    Get ReportService instance (singleton).
    
    CRITICAL: Returns pre-initialized service, does NOT create new instances.
    This ensures ReportService is created ONCE and reused.
    
    Raises:
        RuntimeError: If services not initialized (should not happen in production)
    """
    if _report_service is None:
        raise RuntimeError("Services not initialized. Call initialize_services() at app startup.")
    return _report_service


def cleanup_services() -> None:
    """
    Cleanup services at app shutdown.
    """
    global _query_service, _report_service
    _query_service = None
    _report_service = None
    logger.info("Services cleaned up")

