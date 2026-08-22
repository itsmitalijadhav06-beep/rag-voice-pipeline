"""
Groq LLM client using the existing `httpx` dependency (OpenAI-compatible chat completions API).

Endpoint: https://api.groq.com/openai/v1/chat/completions
Auth:     Authorization: Bearer <LLM_API_KEY>
Output:   JSON object mode (response_format={"type":"json_object"})
"""

from typing import Dict, List

import httpx
import json

from app.generation.config import GenerationConfig, get_generation_config
from app.generation.llm import BaseLLMGenerator, RetryableGenerationError
from app.core.exceptions import GenerationError


class GroqGenerator(BaseLLMGenerator):
    """Concrete generator backed by the Groq REST API."""

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        api_url: str = "https://api.groq.com/openai/v1/chat/completions",
        cfg: GenerationConfig = None,
    ) -> None:
        super().__init__(cfg or get_generation_config())
        self.api_key = api_key if api_key is not None else self.cfg.llm_api_key
        self.model = model if model is not None else self.cfg.llm_model
        self.api_url = api_url

    async def _call_llm(self, messages: List[dict], chunks=None) -> Dict:
        if not self.api_key or not self.api_key.strip():
            raise GenerationError("Groq API key is not configured (LLM_API_KEY).")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.cfg.llm_temperature,
            "max_tokens": self.cfg.llm_max_tokens,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=self.cfg.llm_timeout_s) as client:
                response = await client.post(self.api_url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise RetryableGenerationError("Groq request timed out") from exc
        except httpx.RequestError as exc:
            raise RetryableGenerationError(f"Groq network error: {exc}") from exc

        if response.status_code in (401, 403):
            raise GenerationError("Groq authentication failed (invalid API key).")
        if 400 <= response.status_code < 500:
            raise GenerationError(
                f"Groq request error (HTTP {response.status_code}): "
                f"{response.text[:200]}"
            )
        if response.status_code >= 500:
            raise RetryableGenerationError(
                f"Groq server error (HTTP {response.status_code})"
            )

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage")
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise RetryableGenerationError(
                "Malformed Groq response payload"
            ) from exc

        return {"content": content, "usage": usage}
