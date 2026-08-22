"""
Optional live Groq integration test.

Skipped unless a real LLM_API_KEY is configured via the project's settings (`.env`).
No manual key export is required; the project's existing configuration mechanism is used.
"""

import pytest

from app.core.config import settings
from app.generation import generate
from app.generation.config import is_llm_configured
from app.schemas import ContextChunk

pytestmark = pytest.mark.skipif(
    not is_llm_configured(),
    reason="LLM_API_KEY not configured via project settings; skipping live Groq test",
)


def _chunk(text: str = "The capital of France is Paris.") -> ContextChunk:
    return ContextChunk(chunk_id="chunk-1", text=text, score=0.9, strategy_used="semantic")


@pytest.mark.asyncio
async def test_live_groq_grounded_answer():
    chunks = [_chunk()]
    result = await generate(
        "What is the capital of France according to the context?",
        chunks,
        provider="groq",
    )
    assert isinstance(result.answer, str)
    assert result.latency_ms >= 0.0
