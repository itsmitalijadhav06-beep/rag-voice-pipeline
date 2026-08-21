"""
Generation Package providing LLM orchestration, structured grounding, and prompt synthesis.
"""

from abc import ABC, abstractmethod
from typing import List
from app.schemas import ContextChunk


class BaseGenerator(ABC):
    """Abstract Base Class for LLM Generation Service."""

    @abstractmethod
    async def generate_answer(self, query: str, context_chunks: List[ContextChunk]) -> str:
        """Synthesize answer strictly grounded in retrieved context chunks."""
        pass
