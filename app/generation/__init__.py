"""
Generation Package providing LLM orchestration, structured grounding, and prompt synthesis.

Public entrypoint for the rest of the pipeline:

    from app.generation import generate, GenerationResult
    result = await generate(query, chunks)

`chunks` are expected to be a list of the shared `ContextChunk` objects produced by the
retrieval layer; this package never performs retrieval or STT itself.
"""

from typing import List, Optional

from app.core.exceptions import GenerationError
from app.generation.config import GenerationConfig, get_generation_config
from app.generation.harness import run_generation
from app.generation.llm import BaseLLMGenerator
from app.generation.models import GenerationResult
from app.schemas import ContextChunk

__all__ = [
    "BaseGenerator",
    "BaseLLMGenerator",
    "GenerationResult",
    "get_generator",
    "generate",
]


class BaseGenerator(BaseLLMGenerator):
    """Alias base class for LLM generation services (kept for backward-compatible naming)."""


def get_generator(provider: Optional[str] = None, cfg: Optional[GenerationConfig] = None) -> BaseLLMGenerator:
    """Factory returning a configured generator. Mirrors the STT factory pattern."""
    cfg = cfg or get_generation_config()
    chosen = (provider or cfg.llm_provider).lower()

    if chosen == "mock":
        from app.generation.mock import MockGenerator

        return MockGenerator(cfg=cfg)
    if chosen == "groq":
        from app.generation.groq import GroqGenerator

        return GroqGenerator(cfg=cfg)
    raise GenerationError(f"Unknown generation provider '{chosen}'.")


async def generate(
    query: str,
    chunks: List[ContextChunk],
    provider: Optional[str] = None,
    generator: Optional[BaseLLMGenerator] = None,
    cfg: Optional[GenerationConfig] = None,
) -> GenerationResult:
    """Top-level generation entrypoint used by the final API integration."""
    cfg = cfg or get_generation_config()
    gen = generator or get_generator(provider, cfg)
    return await run_generation(query, chunks, generator=gen, cfg=cfg)
