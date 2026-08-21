"""
Guardrails Package handling input safety, off-topic detection, groundedness verification, and refusal logic.
"""

from abc import ABC, abstractmethod
from typing import List
from app.schemas import GuardrailCheckResult, ContextChunk


class BaseGuardrail(ABC):
    """Abstract Base Class for Pipeline Guardrails."""

    @abstractmethod
    def validate_input(self, query: str) -> GuardrailCheckResult:
        """Validate input query for safety and topic relevance."""
        pass

    @abstractmethod
    def validate_output(
        self, query: str, answer: str, context_chunks: List[ContextChunk]
    ) -> GuardrailCheckResult:
        """Validate output answer for groundedness and hallucination prevention."""
        pass
