"""
Logging Configuration Module

This module sets up structured logging for the application.
It provides:
1. Structured logging (JSON format for production)
2. Configurable log levels
3. Console and file handlers
4. Proper formatting for development and production

Key Concepts:
- Structured Logging: Logs in JSON format (easy to parse, search)
- Log Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Handlers: Where logs go (console, file)
- Formatters: How logs look
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
from app.config import get_settings


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    json_format: Optional[bool] = None
) -> None:
    """
    Set up application-wide logging configuration
    
    This function configures logging for the entire application.
    It should be called once at application startup.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  If None, uses settings.debug to determine
        log_file: Path to log file (optional)
                 If None, logs only to console
        json_format: Whether to use JSON format (for production)
                    If None, uses settings.debug to determine
    """
    settings = get_settings()
    
    # Determine log level
    if log_level is None:
        log_level = "DEBUG" if settings.debug else "INFO"
    
    # Determine format
    if json_format is None:
        json_format = not settings.debug  # JSON in production, pretty in dev
    
    # Use log_file from settings if not provided
    if log_file is None:
        log_file = settings.log_file
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.setLevel(numeric_level)
    
    # Create formatters
    if json_format:
        formatter = create_json_formatter()
    else:
        formatter = create_console_formatter()
    
    # Console handler (always add)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if log_file specified)
    if log_file:
        file_handler = create_file_handler(log_file, numeric_level, json_format)
        root_logger.addHandler(file_handler)
    
    # Set levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Log that logging is configured
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={log_level}, json={json_format}")


def create_console_formatter() -> logging.Formatter:
    """
    Create formatter for console output (development)
    
    Creates a human-readable format with colors and timestamps.
    Good for development and debugging.
    
    Returns:
        Formatter: Console formatter
    """
    return logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def create_json_formatter() -> logging.Formatter:
    """
    Create JSON formatter for structured logging (production)
    
    Creates JSON format that's easy to parse and search.
    Good for production, log aggregation tools (ELK, Splunk, etc.)
    
    Returns:
        Formatter: JSON formatter
    """
    import json
    from datetime import datetime
    
    class JSONFormatter(logging.Formatter):
        """Custom JSON formatter"""
        
        def format(self, record: logging.LogRecord) -> str:
            """Format log record as JSON"""
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }
            
            # Add exception info if present
            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)
            
            # Add extra fields if present
            if hasattr(record, "extra"):
                log_data.update(record.extra)
            
            return json.dumps(log_data)
    
    return JSONFormatter()


def create_file_handler(
    log_file: str,
    level: int,
    json_format: bool
) -> RotatingFileHandler:
    """
    Create rotating file handler
    
    Rotating handler automatically rotates log files when they get too large.
    This prevents log files from growing indefinitely.
    
    Args:
        log_file: Path to log file
        level: Logging level
        json_format: Whether to use JSON format
    
    Returns:
        RotatingFileHandler: File handler
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create rotating file handler
    handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,                # Keep 5 backup files
        encoding='utf-8'
    )
    handler.setLevel(level)
    
    # Set formatter
    if json_format:
        handler.setFormatter(create_json_formatter())
    else:
        handler.setFormatter(create_console_formatter())
    
    return handler


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module
    
    This is a convenience function that follows best practices:
    - Use module name as logger name
    - Logger hierarchy (parent.child)
    
    Usage:
        from app.config.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("This is a log message")
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger: Logger instance
    """
    return logging.getLogger(name)


# ============================================================================
# Explanation of Logging Concepts
# ============================================================================

"""
Logging Levels (from least to most severe):

1. DEBUG: Detailed information for debugging
   Example: "Processing user request with ID: 12345"

2. INFO: General informational messages
   Example: "User logged in successfully"

3. WARNING: Something unexpected happened, but app can continue
   Example: "API rate limit approaching"

4. ERROR: Error occurred, but app can continue
   Example: "Failed to connect to database, retrying..."

5. CRITICAL: Serious error, app may not be able to continue
   Example: "Database connection lost, cannot continue"

When to use each:
- DEBUG: Development, troubleshooting
- INFO: Normal operation, important events
- WARNING: Unexpected but handled situations
- ERROR: Errors that are caught and handled
- CRITICAL: Unrecoverable errors

Logger Hierarchy:
- Root logger: logging.getLogger()
- Module logger: logging.getLogger("app.services")
- Child logger: logging.getLogger("app.services.query_service")

Child loggers inherit settings from parent loggers.
"""

