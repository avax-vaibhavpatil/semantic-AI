"""
Settings Configuration Module

This file centralizes all application configuration using Pydantic BaseSettings.
Benefits:
1. Type safety - Python knows the types of each setting
2. Validation - Automatically validates values
3. Environment-aware - Reads from .env file or environment variables
4. Single source of truth - All config in one place

How it works:
- Pydantic BaseSettings automatically reads from:
  1. Environment variables (highest priority)
  2. .env file (if exists)
  3. Default values (lowest priority)
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Load .env file from current directory or parent directory
# This ensures .env is loaded before Pydantic tries to read it
current_dir = Path(__file__).parent.parent.parent.parent  # Go up to project root
env_file = current_dir / ".env"
if env_file.exists():
    load_dotenv(env_file, override=True)
else:
    # Try current working directory
    load_dotenv(override=True)


class Settings(BaseSettings):
    """
    Application Settings
    
    This class holds all configuration for the application.
    Each field represents one configuration setting.
    """
    
    # ============================================================================
    # API Configuration
    # ============================================================================
    api_title: str = Field(
        default="Auto Semantic BI Platform",
        description="API title for documentation"
    )
    api_version: str = Field(
        default="v1",
        description="API version"
    )
    api_host: str = Field(
        default="0.0.0.0",
        description="Host to bind the API server"
    )
    api_port: int = Field(
        default=8000,
        description="Port to bind the API server"
    )
    
    # ============================================================================
    # Database Configuration
    # ============================================================================
    database_url: str = Field(
        ...,
        description="Database connection URL (REQUIRED)"
    )
    # Example: postgresql://user:password@localhost:5432/dbname
    
    # ============================================================================
    # AI Provider Configuration
    # ============================================================================
    # Preferred AI provider: "groq", "openai", or "anthropic"
    preferred_ai: str = Field(
        default="groq",
        description="Preferred AI provider"
    )
    ai_timeout_seconds: float = Field(
        default=120.0,
        ge=1.0,
        le=300.0,
        description="Timeout for AI provider calls (seconds) - increased for complex queries"
    )
    sql_timeout_seconds: float = Field(
        default=60.0,
        ge=1.0,
        le=600.0,
        description="Timeout for SQL query execution (seconds)"
    )
    
    # Groq API (Fast, free tier available)
    groq_api_key: Optional[str] = Field(
        default=None,
        description="Groq API key"
    )
    groq_model: str = Field(
        default="llama-3.1-8b-instant",
        description="Groq model to use"
    )
    
    # OpenAI API
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key"
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model to use"
    )
    
    # Anthropic (Claude) API
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key"
    )
    anthropic_model: str = Field(
        default="claude-3-haiku-20240307",
        description="Anthropic model to use (Claude 3 Haiku - fast, cost-effective, works well for SQL generation)"
    )
    
    # ============================================================================
    # Semantic Layer Configuration
    # ============================================================================
    semantic_json_path: str = Field(
        default="backend/metadata/semantic.json",
        description="Path to semantic layer JSON file"
    )
    
    # ============================================================================
    # Application Behavior
    # ============================================================================
    max_query_rows: int = Field(
        default=500,
        description="Maximum rows to return from queries"
    )
    
    debug: bool = Field(
        default=False,
        description="Enable debug mode (more verbose logging)"
    )
    
    # ============================================================================
    # Logging Configuration
    # ============================================================================
    log_file: Optional[str] = Field(
        default=None,
        description="Path to log file (optional). If None, logs only to console. Example: 'logs/app.log'"
    )
    
    # ============================================================================
    # CORS Configuration
    # ============================================================================
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins"
    )
    
    # ============================================================================
    # Pydantic Configuration
    # ============================================================================
    class Config:
        """
        Pydantic configuration
        
        Note: .env file is loaded manually above using python-dotenv
        This ensures it works whether running from backend/ or project root.
        
        env_file_encoding: Encoding for .env file
        case_sensitive: Environment variable names are case-insensitive
        """
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Don't set env_file here since we load it manually above


# ============================================================================
# Global Settings Instance
# ============================================================================

# Create a single instance of Settings
# This will be imported and used throughout the application
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings (Singleton pattern)
    
    This function ensures we only create one Settings instance.
    Benefits:
    - Efficient (only loads once)
    - Consistent (same config everywhere)
    
    Usage:
        from app.config import get_settings
        settings = get_settings()
        db_url = settings.database_url
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# ============================================================================
# Validation Helper
# ============================================================================

def validate_settings() -> None:
    """
    Validate that required settings are present
    
    This function checks that critical settings are configured.
    Call this at application startup.
    
    Raises:
        ValueError: If required settings are missing
    """
    settings = get_settings()
    
    # Check database URL
    if not settings.database_url:
        raise ValueError("DATABASE_URL is required but not set")
    
    # Check at least one AI provider is configured
    has_ai_provider = any([
        settings.groq_api_key,
        settings.openai_api_key,
        settings.anthropic_api_key
    ])
    
    if not has_ai_provider:
        raise ValueError(
            "At least one AI provider API key is required. "
            "Set GROQ_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY"
        )

