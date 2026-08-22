"""
Refusal handling: produces a safe, policy-compliant `GenerationResult` when the pipeline
decides not to answer. Refusals are treated as grounded (a safe policy decision), never as an
answer derived from general knowledge.
"""

from typing import Optional

from app.generation.models import GenerationResult

# Canonical guardrail states (informational; surfaced via refusal_reason).
STATE_UNSAFE = "UNSAFE"
STATE_OFF_TOPIC = "OFF_TOPIC"
STATE_INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"
STATE_UNGROUNDED = "UNGROUNDED"

_REFUSAL_MESSAGES = {
    STATE_UNSAFE: "I'm unable to respond to that request.",
    STATE_OFF_TOPIC: "That question is outside the scope of the available information.",
    STATE_INSUFFICIENT_CONTEXT: (
        "I cannot answer this because the retrieved context does not contain "
        "enough information to support a response."
    ),
    STATE_UNGROUNDED: (
        "I cannot provide a confident answer; the response would not be grounded "
        "in the retrieved context."
    ),
}


def build_refusal(
    state: str,
    reason: Optional[str] = None,
    model: str = "policy",
    answer: Optional[str] = None,
) -> GenerationResult:
    """Build a safe refusal `GenerationResult`.

    Refusals are treated as grounded (a safe policy decision), never as an answer
    derived from general knowledge. `answer` lets callers preserve a model-issued
    refusal message instead of the canned one.
    """
    if answer is not None:
        message = answer
    else:
        message = _REFUSAL_MESSAGES.get(state, "I'm unable to answer that request.")
        if reason:
            message = f"{message} ({reason})"
    return GenerationResult(
        answer=message,
        grounded=False,
        citations=[],
        refusal=True,
        refusal_reason=state,
        model=model,
        latency_ms=0.0,
        token_usage=None,
        raw_response=None,
    )
