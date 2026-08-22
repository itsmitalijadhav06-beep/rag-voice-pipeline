"""
Grounding guardrail: verifies a generated answer is supported by the retrieved context.

Practical approach with NO extra LLM call:
  1. A policy refusal (grounded=True, refusal=True) is considered acceptable.
  2. Every cited chunk_id must actually exist in the supplied chunks.
  3. Lexical overlap: a minimum fraction of the answer's content tokens must appear in the
     cited (or all) context chunks. Below the threshold -> UNGROUNDED.
  4. Honors the generator's own `grounded=False` signal.
"""

import re
from typing import List, Optional, Set

from app.generation.config import GenerationConfig, get_generation_config
from app.schemas import ContextChunk, GuardrailCheckResult

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for", "with", "is",
    "are", "was", "were", "be", "been", "being", "that", "this", "it", "as", "at", "by",
    "from", "can", "cannot", "not", "no", "yes", "do", "does", "did", "you", "your",
    "we", "they", "he", "she", "his", "her", "their", "i", "me", "my", "our", "us",
}


def _tokenize(text: str) -> List[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOPWORDS]


class GroundingGuardrail:
    """Validates answer groundedness using citations + lexical overlap."""

    def __init__(self, cfg: Optional[GenerationConfig] = None) -> None:
        self.cfg = cfg or get_generation_config()

    def validate_output(
        self,
        query: str,
        answer: str,
        chunks: List[ContextChunk],
        grounded: bool = True,
        refusal: bool = False,
        citations: Optional[List[str]] = None,
    ) -> GuardrailCheckResult:
        citations = citations or []
        # A safe policy refusal is acceptable (not an ungrounded answer).
        if refusal:
            return GuardrailCheckResult(
                passed=True, reason="Refusal is policy-safe", grounded=True
            )

        if not grounded:
            return GuardrailCheckResult(
                passed=False,
                reason="Generator reported answer is not grounded",
                grounded=False,
            )

        if not chunks:
            return GuardrailCheckResult(
                passed=False, reason="No context to ground the answer", grounded=False
            )

        chunk_by_id = {c.chunk_id: c for c in chunks}
        # Validate cited chunks exist.
        if citations:
            missing = [cid for cid in citations if cid not in chunk_by_id]
            if missing:
                return GuardrailCheckResult(
                    passed=False,
                    reason=f"Citation refers to unknown chunk(s): {missing}",
                    grounded=False,
                )
            context_text = " ".join(chunk_by_id[cid].text for cid in citations)
        else:
            context_text = " ".join(c.text for c in chunks)

        answer_tokens: Set[str] = set(_tokenize(answer))
        if not answer_tokens:
            return GuardrailCheckResult(
                passed=False, reason="Answer contains no verifiable content", grounded=False
            )

        context_tokens: Set[str] = set(_tokenize(context_text))
        overlap = len(answer_tokens & context_tokens) / len(answer_tokens)
        if overlap < self.cfg.guardrail_min_overlap:
            return GuardrailCheckResult(
                passed=False,
                reason=f"Answer groundedness {overlap:.2f} below threshold "
                f"{self.cfg.guardrail_min_overlap:.2f}",
                grounded=False,
            )

        return GuardrailCheckResult(passed=True, grounded=True)
