"""
Claude Provider (Anthropic)
"""

import os
from typing import Optional
import anthropic
from anthropic import RateLimitError, APIStatusError, APIConnectionError, APITimeoutError
from app.infrastructure.ai.base import AIProvider, RetryableAIError, ValidationAIError, is_retryable_status


class ClaudeProvider(AIProvider):
    name = "claude"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        # Get API key from parameter, environment variable, or None
        # NEVER hardcode API keys in source code - use environment variables
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        
        # Primary model: Claude 3 Haiku (tested and working with current API key)
        # Haiku is fast, cost-effective, and works well for SQL generation
        self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        
        self.client = None
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)

    def is_configured(self) -> bool:
        return bool(self.api_key and self.client)

    def generate_sql(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> str:
        if not self.is_configured():
            raise ValidationAIError("Claude provider not configured")

        try:
            # Anthropic requires "messages" with system + user
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            # Claude returns content list; take first text block
            if not resp.content:
                raise ValidationAIError("Claude returned empty response")
            # Extract text parts
            text_parts = [c.text for c in resp.content if hasattr(c, "text")]
            if not text_parts:
                raise ValidationAIError("Claude response missing text content")
            return "\n".join(text_parts).strip()

        except (APITimeoutError, RateLimitError, APIConnectionError) as e:
            raise RetryableAIError(str(e)) from e
        except APIStatusError as e:
            if is_retryable_status(getattr(e, "status_code", None)):
                raise RetryableAIError(str(e)) from e
            raise ValidationAIError(str(e)) from e
        except Exception as e:  # pragma: no cover
            raise RetryableAIError(str(e)) from e

