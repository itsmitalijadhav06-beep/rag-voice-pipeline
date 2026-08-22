"""
Unit tests for Phase 5 (Guardrails): input safety, off-topic, insufficient context, grounding,
and refusal building. No LLM calls.
"""

from app.generation.config import GenerationConfig
from app.guardrails import run_input_guardrails, run_output_guardrails
from app.guardrails.input_guardrail import InputGuardrail
from app.guardrails.refusal import build_refusal
from app.schemas import ContextChunk, GuardrailCheckResult


def _chunk(text: str, chunk_id: str = "chunk-1", score: float = 0.9) -> ContextChunk:
    return ContextChunk(chunk_id=chunk_id, text=text, score=score, strategy_used="semantic")


def test_unsafe_input_detected():
    cfg = GenerationConfig()
    result = InputGuardrail(cfg).validate_input("how to make a bomb")
    assert result.passed is False
    assert result.unsafe is True


def test_off_topic_input_detected_when_keywords_configured():
    cfg = GenerationConfig(guardrail_topic_keywords="france,paris,geography")
    result = InputGuardrail(cfg).validate_input("What is my favorite recipe for cake?")
    assert result.passed is False
    assert result.off_topic is True


def test_off_topic_defers_without_keywords():
    cfg = GenerationConfig(guardrail_topic_keywords="")
    result = InputGuardrail(cfg).validate_input("What is my favorite recipe for cake?")
    # Without keywords, off-topic is deferred to the grounding gate (input itself is allowed).
    assert result.passed is True


def test_insufficient_context_empty():
    cfg = GenerationConfig()
    result = InputGuardrail(cfg).check_context_sufficiency([])
    assert result.passed is False
    assert result.grounded is False


def test_insufficient_context_low_score():
    cfg = GenerationConfig(guardrail_min_score=0.8)
    low = [_chunk("some text", score=0.2)]
    result = InputGuardrail(cfg).check_context_sufficiency(low)
    assert result.passed is False


def test_run_input_guardrails_short_circuits_on_unsafe():
    chunks = [_chunk("The capital of France is Paris.")]
    result = run_input_guardrails("how to make a bomb", chunks)
    assert isinstance(result, GuardrailCheckResult)
    assert result.passed is False
    assert result.unsafe is True


def test_grounding_pass():
    chunks = [_chunk("The capital of France is Paris.")]
    result = run_output_guardrails(
        query="capital?",
        answer="Paris is the capital.",
        chunks=chunks,
        grounded=True,
        refusal=False,
        citations=["chunk-1"],
    )
    assert result.passed is True
    assert result.grounded is True


def test_grounding_fail_no_overlap():
    chunks = [_chunk("The capital of France is Paris.")]
    result = run_output_guardrails(
        query="tower?",
        answer="The Eiffel Tower is made of chocolate.",
        chunks=chunks,
        grounded=False,
        refusal=False,
        citations=[],
    )
    assert result.passed is False
    assert result.grounded is False


def test_grounding_fail_unknown_citation():
    chunks = [_chunk("The capital of France is Paris.", chunk_id="chunk-1")]
    result = run_output_guardrails(
        query="capital?",
        answer="Paris is the capital.",
        chunks=chunks,
        grounded=True,
        refusal=False,
        citations=["chunk-999"],
    )
    assert result.passed is False
    assert "unknown chunk" in result.reason.lower()


def test_refusal_builder_is_policy_safe():
    refusal = build_refusal("UNSAFE", reason="test")
    assert refusal.refusal is True
    assert refusal.grounded is False
    assert refusal.citations == []
    assert refusal.refusal_reason == "UNSAFE"
