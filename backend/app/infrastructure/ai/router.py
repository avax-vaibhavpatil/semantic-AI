"""
Provider Router with Fallback

Attempts providers in priority order with retryable error handling.
"""

from typing import List, Optional
from app.infrastructure.ai.base import AIProvider, RetryableAIError, ValidationAIError


class ProviderRouter:
    """
    Routes requests across multiple providers with fallback.

    Fallback triggers only on retryable errors (timeouts, 5xx, 429, connection errors).
    """

    def __init__(self, providers: List[AIProvider]):
        # Keep only configured providers, preserve priority order
        self.providers = [p for p in providers if p.is_configured()]

    def generate_sql(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> str:
        if not self.providers:
            raise ValidationAIError("No AI providers are configured")

        last_error: Optional[Exception] = None

        for idx, provider in enumerate(self.providers):
            is_last = idx == len(self.providers) - 1
            try:
                return provider.generate_sql(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except ValidationAIError as e:
                # Non-retryable, bubble up immediately
                raise e
            except RetryableAIError as e:
                last_error = e
                # Try next provider if available
                if is_last:
                    raise e
                continue
            except Exception as e:  # pragma: no cover
                last_error = e
                if is_last:
                    raise e
                continue

        # If we exhausted providers, raise last error
        if last_error:
            raise last_error
        raise ValidationAIError("No provider succeeded")


def build_default_router() -> ProviderRouter:
    """
    Build a router with OpenAI (currently active).
    Only providers with configured keys are included.
    
    NOTE: Claude is commented out but can be easily re-enabled.
    To switch back to Claude:
    1. Comment out OpenAIProvider
    2. Uncomment ClaudeProvider
    3. Update preferred_ai in settings.py to "anthropic"
    """
    # Currently using OpenAI
    from app.infrastructure.ai.providers.openai_provider import OpenAIProvider
    from app.config import get_settings
    
    # Claude provider (commented out - can be re-enabled in future)
    # from app.infrastructure.ai.providers.claude_provider import ClaudeProvider

    settings = get_settings()
    providers: List[AIProvider] = [
        OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model
        ),  # Currently active
        # ClaudeProvider(
        #     api_key=settings.anthropic_api_key,
        #     model=settings.anthropic_model
        # ),  # Commented out - uncomment to switch back to Claude
    ]
    return ProviderRouter(providers)

