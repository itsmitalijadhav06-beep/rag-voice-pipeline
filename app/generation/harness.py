"""
Reliability harness for the generation/guardrail portion of the pipeline.

Responsibilities:
  * Run input + context-sufficiency guardrails (short-circuit, no LLM call on reject).
  * Call the generator with bounded exponential backoff over transient failures.
  * Run output grounding; retry once on ungrounded output, then refuse.
  * Record latency via the shared `LatencyTracker` and attach `latency_ms`.

It does NOT call retrieval or STT; `chunks` are passed in pre-resolved.
"""

import asyncio
import time
from typing import List, Optional

from app.analytics import latency_tracker
from app.core.exceptions import GenerationError
from app.core.logging import logger
from app.generation.config import GenerationConfig, get_generation_config
from app.generation.llm import BaseLLMGenerator, RetryableGenerationError
from app.generation.models import GenerationResult
from app.guardrails.refusal import (
    STATE_INSUFFICIENT_CONTEXT,
    STATE_OFF_TOPIC,
    STATE_UNGROUNDED,
    STATE_UNSAFE,
    build_refusal,
)
from app.guardrails import run_input_guardrails, run_output_guardrails
from app.schemas import ContextChunk

__all__ = ["run_generation"]


def _map_input_state(result) -> str:
    if result.unsafe:
        return STATE_UNSAFE
    if result.off_topic:
        return STATE_OFF_TOPIC
    return STATE_INSUFFICIENT_CONTEXT


async def run_generation(
    query: str,
    chunks: List[ContextChunk],
    generator: Optional[BaseLLMGenerator] = None,
    cfg: Optional[GenerationConfig] = None,
) -> GenerationResult:
    cfg = cfg or get_generation_config()
    generator = generator or _default_generator(cfg)

    # 1. Input + context-sufficiency guardrails (no LLM call on rejection).
    input_guard_start = time.perf_counter()
    logger.info("[QUERY] run_generation: input guardrails start")
    input_check = run_input_guardrails(query, chunks, cfg)
    input_guard_ms = (time.perf_counter() - input_guard_start) * 1000
    logger.info("[QUERY] run_generation: input guardrails complete (%.2f ms, passed=%s)", input_guard_ms, input_check.passed)

    if not input_check.passed:
        state = _map_input_state(input_check)
        logger.info("Input guardrail rejected query: state=%s reason=%s", state, input_check.reason)
        res = build_refusal(state, reason=input_check.reason)
        res.guardrail_latency_ms = input_guard_ms
        return res

    # 2. Generation with bounded exponential backoff.
    attempts = cfg.llm_max_retries + 1
    delay = cfg.llm_backoff_base_s
    result: Optional[GenerationResult] = None
    start = time.perf_counter()

    for attempt in range(attempts):
        try:
            logger.info("[QUERY] run_generation: LLM generate attempt %d/%d start", attempt + 1, attempts)
            attempt_start = time.perf_counter()
            result = await generator.generate(query, chunks)
            logger.info("[QUERY] run_generation: LLM generate attempt %d/%d complete (%.2f ms)", attempt + 1, attempts, (time.perf_counter() - attempt_start) * 1000)
            break
        except RetryableGenerationError as exc:
            logger.warning(
                "Generation attempt %d/%d failed (retryable): %s (took %.2f ms)",
                attempt + 1,
                attempts,
                exc.message if hasattr(exc, "message") else exc,
                (time.perf_counter() - attempt_start) * 1000
            )
            if attempt == attempts - 1:
                latency_tracker.record_latency((time.perf_counter() - start) * 1000)
                res = build_refusal(
                    STATE_UNGROUNDED, reason="Generation failed after retries"
                )
                res.guardrail_latency_ms = input_guard_ms
                return res
            await asyncio.sleep(min(delay, cfg.llm_backoff_max_s))
            delay *= 2
        except GenerationError as exc:
            logger.error(
                "Generation attempt %d/%d failed (permanent): %s",
                attempt + 1,
                attempts,
                exc.message if hasattr(exc, "message") else exc,
            )
            latency_tracker.record_latency((time.perf_counter() - start) * 1000)
            res = build_refusal(STATE_UNGROUNDED, reason="Generation provider error")
            res.guardrail_latency_ms = input_guard_ms
            return res

    # 3. Output grounding verification.
    assert result is not None

    # A model-issued refusal is policy-safe (consistent with the grounding guardrail),
    # so normalize it to grounded=True rather than propagating the model's grounded=False.
    if result.refusal:
        latency_tracker.record_latency((time.perf_counter() - start) * 1000)
        res = build_refusal(
            state=result.refusal_reason or "refusal",
            reason=result.refusal_reason,
            model=result.model,
            answer=result.answer,
        )
        res.guardrail_latency_ms = input_guard_ms
        return res

    output_guard_start = time.perf_counter()
    grounding = run_output_guardrails(
        query=query,
        answer=result.answer,
        chunks=chunks,
        grounded=result.grounded,
        refusal=result.refusal,
        citations=result.citations,
        cfg=cfg,
    )
    output_guard_ms = (time.perf_counter() - output_guard_start) * 1000
    total_guard_ms = input_guard_ms + output_guard_ms

    if not grounding.passed and not result.refusal:
        # One stricter re-generation attempt, then refuse if still ungrounded.
        logger.info("Grounding failed; retrying generation once.")
        try:
            retry = await generator.generate(query, chunks)
        except RetryableGenerationError:
            retry = None
        if retry is not None:
            output_guard_retry_start = time.perf_counter()
            recheck = run_output_guardrails(
                query=query,
                answer=retry.answer,
                chunks=chunks,
                grounded=retry.grounded,
                refusal=retry.refusal,
                citations=retry.citations,
                cfg=cfg,
            )
            retry_guard_ms = (time.perf_counter() - output_guard_retry_start) * 1000
            total_guard_ms += retry_guard_ms

            if recheck.passed or retry.refusal:
                latency_tracker.record_latency((time.perf_counter() - start) * 1000)
                retry.guardrail_latency_ms = total_guard_ms
                return retry

        latency_tracker.record_latency((time.perf_counter() - start) * 1000)
        res = build_refusal(STATE_UNGROUNDED, reason="Answer not grounded in context")
        res.guardrail_latency_ms = total_guard_ms
        return res

    latency_tracker.record_latency((time.perf_counter() - start) * 1000)
    result.guardrail_latency_ms = total_guard_ms
    return result


def _default_generator(cfg: GenerationConfig) -> BaseLLMGenerator:
    from app.generation.groq import GroqGenerator

    return GroqGenerator(cfg=cfg)
