"""
Provider-agnostic base generator: builds prompts, calls the provider, parses and validates
the structured JSON response, and wraps it in a `GenerationResult`.
"""

import json
import re
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from pydantic import ValidationError

from app.core.exceptions import GenerationError
from app.core.logging import logger
from app.generation.config import GenerationConfig, get_generation_config
from app.generation.models import GenerationResult, StructuredGenerationOutput
from app.generation.prompts import build_messages
from app.schemas import ContextChunk


class RetryableGenerationError(GenerationError):
    """Transient generation failure that the harness may retry with backoff."""


class BaseLLMGenerator(ABC):
    """Base class implementing shared generation + structured-output parsing."""

    def __init__(self, cfg: Optional[GenerationConfig] = None) -> None:
        self.cfg = cfg or get_generation_config()

    @abstractmethod
    async def _call_llm(self, messages: List[dict], chunks: List[ContextChunk]) -> Dict:
        """
        Call the underlying LLM and return a dict with at least:
            {"content": str, "usage": Optional[Dict[str, int]]}
        `chunks` are provided so subclasses may use context (e.g. for deterministic mocks).
        Implementations should raise `RetryableGenerationError` for transient failures
        (timeout, network, 5xx, malformed output) and `GenerationError` for permanent
        failures (auth, 4xx).
        """

    async def generate(self, query: str, chunks: List[ContextChunk]) -> GenerationResult:
        messages = build_messages(query, chunks)
        start = time.perf_counter()
        try:
            resp = await self._call_llm(messages, chunks)
        except (GenerationError, RetryableGenerationError):
            raise

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        raw = resp.get("content", "") if isinstance(resp, dict) else ""
        parsed = self._parse_structured(raw)
        usage = self._normalize_usage(resp.get("usage")) if isinstance(resp, dict) else None

        return GenerationResult(
            answer=parsed.answer,
            grounded=parsed.grounded,
            citations=parsed.citations,
            refusal=parsed.refusal,
            refusal_reason=parsed.refusal_reason,
            model=self.cfg.llm_model,
            latency_ms=elapsed_ms,
            token_usage=usage,
            raw_response=raw,
        )

    def _parse_structured(self, raw: str) -> StructuredGenerationOutput:
        if not raw or not raw.strip():
            raise RetryableGenerationError("Empty LLM response")

        text = raw.strip()
        # Defensively strip Markdown code fences (e.g. ```json ... ```).
        fence = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if fence:
            text = fence.group(1).strip()
        # Fallback: extract the first balanced {...} block if stray prose is present.
        if not text.startswith("{"):
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                text = text[start : end + 1]

        try:
            data = json.loads(text)
        except (json.JSONDecodeError, ValueError) as exc:
            raise RetryableGenerationError(
                "Malformed LLM response: not valid JSON"
            ) from exc
        if not isinstance(data, dict):
            raise RetryableGenerationError("Malformed LLM response: expected JSON object")
        try:
            return StructuredGenerationOutput(**data)
        except ValidationError as exc:
            raise RetryableGenerationError(
                f"Invalid LLM response schema: {exc}"
            ) from exc

    @staticmethod
    def _normalize_usage(usage) -> Optional[Dict[str, int]]:
        if not isinstance(usage, dict):
            return None
        return {
            "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
            "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
        }
