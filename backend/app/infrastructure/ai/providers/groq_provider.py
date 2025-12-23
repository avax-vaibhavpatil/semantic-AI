"""
Groq Provider

Uses OpenAI-compatible client pointed to Groq API.
"""

import os
from typing import Optional
from openai import OpenAI, APIError, RateLimitError, APITimeoutError
from app.infrastructure.ai.base import AIProvider, RetryableAIError, ValidationAIError, is_retryable_status


class GroqProvider(AIProvider):
    name = "groq"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.model = model or os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
        # Groq uses OpenAI-compatible endpoint
        self.client = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url="https://api.groq.com/openai/v1")

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
            raise ValidationAIError("Groq provider not configured")

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                n=1,
            )
            return resp.choices[0].message.content.strip()

        except (APITimeoutError, RateLimitError) as e:
            raise RetryableAIError(str(e)) from e
        except APIError as e:
            # Retry on 5xx / 429
            if is_retryable_status(getattr(e, "status_code", None)):
                raise RetryableAIError(str(e)) from e
            raise ValidationAIError(str(e)) from e
        except Exception as e:  # pragma: no cover
            # Unknown errors: treat as retryable to allow fallback
            raise RetryableAIError(str(e)) from e

