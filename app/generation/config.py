"""
Local generation configuration.

New generation/retry settings are intentionally defined here (not in `app/core/config.py`)
to avoid modifying the shared, protected configuration module. Existing provider secrets
(`LLM_API_KEY`, `LLM_MODEL`) are reused from `app.core.config.settings`.

All values fall back to sensible defaults so the package works with no extra env setup.
"""

import os
from dataclasses import dataclass, field

from app.core.config import settings

# Matches the placeholder shipped in .env.example so it is never treated as a real key.
PLACEHOLDER_KEY = "your_llm_api_key_here"


def is_llm_configured() -> bool:
    """Return True only when a real LLM API key is present via the project settings.

    Uses the same configuration mechanism as the rest of the app (pydantic-settings
    loading `.env`), with an `os.getenv` fallback. The placeholder value is rejected.
    """
    key = settings.LLM_API_KEY or os.getenv("LLM_API_KEY", "")
    return bool(key) and key.strip() != "" and key != PLACEHOLDER_KEY


@dataclass
class GenerationConfig:
    """Runtime configuration for generation and the reliability harness."""

    llm_api_key: str = field(
        default_factory=lambda: settings.LLM_API_KEY or os.getenv("LLM_API_KEY", "")
    )
    llm_model: str = field(
        default_factory=lambda: settings.LLM_MODEL or os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
    )
    llm_provider: str = field(
        default_factory=lambda: settings.LLM_PROVIDER or os.getenv("LLM_PROVIDER", "groq")
    )
    llm_timeout_s: float = field(
        default_factory=lambda: float(os.getenv("LLM_TIMEOUT_S", "10.0"))
    )
    llm_max_tokens: int = field(
        default_factory=lambda: int(os.getenv("LLM_MAX_TOKENS", "512"))
    )
    llm_temperature: float = field(
        default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.0"))
    )
    llm_max_retries: int = field(
        default_factory=lambda: int(os.getenv("LLM_MAX_RETRIES", "2"))
    )
    llm_backoff_base_s: float = field(
        default_factory=lambda: float(os.getenv("LLM_BACKOFF_BASE_S", "0.2"))
    )
    llm_backoff_max_s: float = field(
        default_factory=lambda: float(os.getenv("LLM_BACKOFF_MAX_S", "2.0"))
    )
    guardrail_min_score: float = field(
        default_factory=lambda: float(os.getenv("GUARDRAIL_MIN_SCORE", "0.0"))
    )
    guardrail_min_overlap: float = field(
        default_factory=lambda: float(os.getenv("GUARDRAIL_MIN_OVERLAP", "0.3"))
    )
    guardrail_topic_keywords: str = field(
        default_factory=lambda: os.getenv("GUARDRAIL_TOPIC_KEYWORDS", "")
    )
    guardrail_score_higher_is_better: bool = field(
        default_factory=lambda: os.getenv("GUARDRAIL_SCORE_HIGHER_IS_BETTER", "true").lower()
        == "true"
    )
    max_context_chunks: int = field(
        default_factory=lambda: int(os.getenv("MAX_CONTEXT_CHUNKS", "10"))
    )
    max_context_chars: int = field(
        default_factory=lambda: int(os.getenv("MAX_CONTEXT_CHARS", "8000"))
    )


def get_generation_config() -> GenerationConfig:
    """Return a `GenerationConfig` populated from environment variables."""
    return GenerationConfig()
