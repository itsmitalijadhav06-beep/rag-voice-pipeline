"""
Pydantic models for LLM generation results and structured output parsing.

`GenerationResult` is the public contract returned by `app.generation.generate` and consumed
by the final API integration. It intentionally lives in this package (not in `app/schemas/`)
to avoid modifying the shared, protected schemas module.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class GenerationResult(BaseModel):
    """Structured result produced by the generation pipeline."""

    answer: str = Field(..., description="Final answer text (or refusal message).")
    grounded: bool = Field(
        ..., description="Whether the answer is supported by retrieved context."
    )
    citations: List[str] = Field(
        default_factory=list,
        description="chunk_ids the answer is grounded in.",
    )
    refusal: bool = Field(
        default=False,
        description="True when the system refused to answer (unsafe/off-topic/insufficient/ungrounded).",
    )
    refusal_reason: Optional[str] = Field(
        None, description="Reason for refusal when refusal is True."
    )
    model: str = Field(..., description="Model identifier that produced the answer.")
    latency_ms: float = Field(
        ..., description="Generation latency in milliseconds (pure LLM call)."
    )
    token_usage: Optional[Dict[str, int]] = Field(
        None, description="Token usage, e.g. {'prompt_tokens': int, 'completion_tokens': int}."
    )
    raw_response: Optional[str] = Field(
        None, description="Raw provider payload, kept for debugging only."
    )


class StructuredGenerationOutput(BaseModel):
    """
    Schema the LLM is instructed to return as JSON.

    Used to validate the model's structured response before wrapping it in a
    `GenerationResult`.
    """

    answer: str
    grounded: bool
    citations: List[str] = Field(default_factory=list)
    refusal: bool = False
    refusal_reason: Optional[str] = None
