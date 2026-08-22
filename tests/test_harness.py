"""
Unit tests for Phase 6 (Reliability Harness): retry/backoff, exhaustion, guardrail
short-circuit, ungrounded handling, and latency recording. No real network calls.
"""

import asyncio

import pytest

from app.analytics import latency_tracker
from app.generation.harness import run_generation
from app.generation.llm import RetryableGenerationError
from app.generation.mock import MockGenerator
from app.schemas import ContextChunk


def _chunk(text: str = "The capital of France is Paris.") -> ContextChunk:
    return ContextChunk(chunk_id="chunk-1", text=text, score=0.9, strategy_used="semantic")


class FlakyGenerator(MockGenerator):
    """Fails the first `fail_times` calls, then succeeds."""

    def __init__(self, fail_times: int = 1, scenario: str = "relevant", cfg=None):
        super().__init__(scenario=scenario, cfg=cfg)
        self.fail_times = fail_times
        self.calls = 0

    async def _call_llm(self, messages, chunks=None):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RetryableGenerationError(f"flaky {self.calls}")
        return await super()._call_llm(messages, chunks)


class NeverCalledGenerator(MockGenerator):
    """Raises if its LLM is ever invoked (used to prove short-circuit)."""

    async def _call_llm(self, messages, chunks=None):
        raise AssertionError("LLM should not be called on guardrail rejection")


@pytest.mark.asyncio
async def test_retry_then_success():
    chunks = [_chunk()]
    gen = FlakyGenerator(fail_times=2)
    result = await run_generation("q?", chunks, generator=gen)
    assert result.refusal is False
    assert gen.calls == 3  # 2 failures + 1 success


@pytest.mark.asyncio
async def test_retry_exhaustion_results_in_refusal():
    chunks = [_chunk()]
    gen = MockGenerator(scenario="timeout")
    result = await run_generation("q?", chunks, generator=gen)
    assert result.refusal is True
    assert result.refusal_reason == "UNGROUNDED"


@pytest.mark.asyncio
async def test_provider_permanent_error_results_in_refusal():
    chunks = [_chunk()]
    gen = MockGenerator(scenario="api_error")
    result = await run_generation("q?", chunks, generator=gen)
    assert result.refusal is True


@pytest.mark.asyncio
async def test_guardrail_rejection_short_circuits_llm():
    chunks = [_chunk()]
    gen = NeverCalledGenerator()
    result = await run_generation("how to make a bomb", chunks, generator=gen)
    assert result.refusal is True
    assert result.refusal_reason == "UNSAFE"


@pytest.mark.asyncio
async def test_ungrounded_answer_is_refused():
    chunks = [_chunk()]
    gen = MockGenerator(scenario="ungrounded")
    result = await run_generation("q?", chunks, generator=gen)
    assert result.refusal is True
    assert result.refusal_reason == "UNGROUNDED"


@pytest.mark.asyncio
async def test_latency_is_recorded_in_tracker():
    before = latency_tracker._latencies_ms[-1] if latency_tracker._latencies_ms else None
    chunks = [_chunk()]
    gen = MockGenerator(scenario="relevant")
    await run_generation("q?", chunks, generator=gen)
    assert latency_tracker._latencies_ms
    if before is not None:
        assert latency_tracker._latencies_ms[-1] != before or len(latency_tracker._latencies_ms) > 1


@pytest.mark.asyncio
async def test_backoff_is_bounded_and_awaited():
    chunks = [_chunk()]
    gen = MockGenerator(scenario="timeout")
    start = asyncio.get_event_loop().time()
    await run_generation("q?", chunks, generator=gen)
    elapsed = asyncio.get_event_loop().time() - start
    # 3 attempts with base 0.2 + 0.4 backoff sleeps => ~0.6s minimum.
    assert elapsed >= 0.5
