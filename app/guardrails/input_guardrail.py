"""
Input guardrail: unsafe content, off-topic content, and insufficient retrieval context.

All checks are lexical/heuristic and require NO extra LLM call. The off-topic check is
pluggable via the `GUARDRAIL_TOPIC_KEYWORDS` env var (comma-separated domain terms); when no
keywords are configured it defers off-topic detection to the grounding gate.
"""

import re
from typing import List, Optional

from app.core.config import settings
from app.generation.config import GenerationConfig, get_generation_config
from app.schemas import ContextChunk, GuardrailCheckResult

# Curated, intentionally small denylist for clearly unsafe / jailbreak-style prompts.
_UNSAFE_PATTERNS = [
    r"\bbomb\b", r"\bweapon\b", r"\bexplosive\b", r"\bhow to (kill|hurt|harm|hack)\b",
    r"\bmake a (virus|malware)\b", r"\bsuicide\b", r"\bself[- ]?harm\b",
    r"\bigNORE (previous|all|prior) instructions\b", r"\bjailbreak\b",
]


class InputGuardrail:
    """Validates query safety / relevance and retrieval sufficiency before generation."""

    def __init__(self, cfg: Optional[GenerationConfig] = None) -> None:
        self.cfg = cfg or get_generation_config()
        self._unsafe_re = re.compile("|".join(_UNSAFE_PATTERNS), re.IGNORECASE)
        raw_keywords = self.cfg.guardrail_topic_keywords or getattr(
            settings, "GUARDRAIL_TOPIC_KEYWORDS", ""
        )
        self._topic_keywords = {
            k.strip().lower() for k in str(raw_keywords).split(",") if k.strip()
        }

    def validate_input(self, query: str) -> GuardrailCheckResult:
        if not query or not query.strip():
            return GuardrailCheckResult(
                passed=False, reason="Empty query", off_topic=True
            )

        if self._unsafe_re.search(query):
            return GuardrailCheckResult(
                passed=False, reason="Unsafe input detected", unsafe=True
            )

        if self._topic_keywords:
            tokens = {t.lower() for t in re.findall(r"[a-z0-9]+", query.lower())}
            if not tokens & self._topic_keywords:
                return GuardrailCheckResult(
                    passed=False, reason="Off-topic input", off_topic=True
                )

        return GuardrailCheckResult(passed=True, grounded=True)

    def check_context_sufficiency(self, chunks: List[ContextChunk]) -> GuardrailCheckResult:
        """Flag INSUFFICIENT_CONTEXT when retrieval returned nothing usable."""
        if not chunks:
            return GuardrailCheckResult(
                passed=False,
                reason="No retrieved context available",
                grounded=False,
            )

        if self.cfg.guardrail_min_score > 0.0:
            # Score is treated as OPTIONAL metadata. Direction is explicit/configurable
            # so correctness never silently depends on an assumed "higher = better".
            # Default is higher-is-better (cosine similarity style).
            usable = [
                c
                for c in chunks
                if isinstance(getattr(c, "score", None), (int, float))
                and (
                    c.score >= self.cfg.guardrail_min_score
                    if self.cfg.guardrail_score_higher_is_better
                    else c.score <= self.cfg.guardrail_min_score
                )
            ]
            if not usable:
                return GuardrailCheckResult(
                    passed=False,
                    reason="Retrieved context scores below threshold",
                    grounded=False,
                )

        return GuardrailCheckResult(passed=True, grounded=True)
