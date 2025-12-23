"""
AI Provider Base Classes and Errors
"""

from abc import ABC, abstractmethod
from typing import Optional


class RetryableAIError(Exception):
    """Error that is safe to retry with another provider (timeouts, 5xx, rate limits)."""


class ValidationAIError(Exception):
    """Non-retryable error (bad request, invalid prompt, too large)."""


class AIProvider(ABC):
    """
    Base class for AI providers.
    Implementations must be synchronous for now (keeps compatibility with current code).
    """

    name: str

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if provider has the required credentials."""

    @abstractmethod
    def generate_sql(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> str:
        """Generate SQL from prompts."""


def is_retryable_status(code: Optional[int]) -> bool:
    """Return True if status code is retryable."""
    if code is None:
        return False
    if code >= 500:
        return True
    if code in (408, 429):  # timeout, rate limit
        return True
    return False

