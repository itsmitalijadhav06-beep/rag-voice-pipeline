"""
Guardrails Package handling input safety, off-topic detection, groundedness verification, and refusal logic.
"""

from typing import List, Optional

from app.generation.config import GenerationConfig, get_generation_config
from app.schemas import ContextChunk, GuardrailCheckResult
from app.guardrails.grounding_guardrail import GroundingGuardrail
from app.guardrails.input_guardrail import InputGuardrail

__all__ = [
    "InputGuardrail",
    "GroundingGuardrail",
    "run_input_guardrails",
    "run_output_guardrails",
]


def run_input_guardrails(
    query: str,
    chunks: List[ContextChunk],
    cfg: Optional[GenerationConfig] = None,
) -> GuardrailCheckResult:
    """Run input + context-sufficiency checks. Returns the first failing result."""
    cfg = cfg or get_generation_config()
    input_guard = InputGuardrail(cfg)
    result = input_guard.validate_input(query)
    if not result.passed:
        return result
    return input_guard.check_context_sufficiency(chunks)


def run_output_guardrails(
    query: str,
    answer: str,
    chunks: List[ContextChunk],
    grounded: bool = True,
    refusal: bool = False,
    citations: Optional[List[str]] = None,
    cfg: Optional[GenerationConfig] = None,
) -> GuardrailCheckResult:
    """Run grounding verification on a generated answer."""
    cfg = cfg or get_generation_config()
    return GroundingGuardrail(cfg).validate_output(
        query=query,
        answer=answer,
        chunks=chunks,
        grounded=grounded,
        refusal=refusal,
        citations=citations,
    )
