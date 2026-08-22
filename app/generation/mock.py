"""
Deterministic mock generator for tests and offline runs.

No network calls. Behaviour is selected via `scenario` so the same class can exercise every
branch (relevant, irrelevant, conflicting, injection, malformed, timeout, network, ungrounded).
"""

from typing import List, Optional

from app.core.exceptions import GenerationError
from app.generation.config import GenerationConfig, get_generation_config
from app.generation.llm import BaseLLMGenerator, RetryableGenerationError
from app.generation.models import GenerationResult
from app.schemas import ContextChunk


class MockGenerator(BaseLLMGenerator):
    """
    Scenario-driven fake generator.

    Scenarios:
      relevant    -> grounded answer citing the first chunk.
      irrelevant  -> refusal (context not relevant).
      conflicting -> answers using the highest-scored chunk, flags grounded.
      injection   -> refuses / ignores injected instructions inside context.
      ungrounded  -> returns an answer that is not supported by context.
      malformed   -> returns invalid JSON (forces parse failure / retry).
      timeout     -> raises RetryableGenerationError (timeout).
      network     -> raises RetryableGenerationError (network).
      api_error   -> raises GenerationError (permanent failure).
    """

    def __init__(
        self,
        scenario: str = "relevant",
        answer: Optional[str] = None,
        cfg: GenerationConfig = None,
    ) -> None:
        super().__init__(cfg or get_generation_config())
        self.scenario = scenario
        self._answer = answer

    async def _call_llm(self, messages: List[dict], chunks=None) -> dict:
        if self.scenario == "timeout":
            raise RetryableGenerationError("Mock timeout")
        if self.scenario == "network":
            raise RetryableGenerationError("Mock network error")
        if self.scenario == "api_error":
            raise GenerationError("Mock permanent API error")

        if self.scenario == "malformed":
            return {"content": "this is not json", "usage": {"prompt_tokens": 1, "completion_tokens": 1}}

        return {
            "content": self._build_json(messages, chunks),
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        }

    def _context_text(self, chunks) -> str:
        if not chunks:
            return ""
        return " ".join(getattr(c, "text", "") for c in chunks)

    def _build_json(self, messages: List[dict], chunks=None) -> str:
        import json

        context = self._context_text(chunks)
        if self._answer is not None:
            answer = self._answer
        elif self.scenario in ("irrelevant", "injection"):
            answer = "I cannot answer that from the provided context."
        elif self.scenario == "ungrounded":
            answer = "The Eiffel Tower is made of chocolate and was built in 1999."
        elif context:
            answer = f"Based on the retrieved context: {context}"
        else:
            answer = "Based on the context, the answer is documented in the retrieved passage."

        behavior = {
            "relevant": {"grounded": True, "refusal": False, "citations": ["chunk-1"]},
            "conflicting": {"grounded": True, "refusal": False, "citations": ["chunk-1"]},
            "irrelevant": {"grounded": False, "refusal": True, "citations": [], "refusal_reason": "insufficient context"},
            "injection": {"grounded": False, "refusal": True, "citations": [], "refusal_reason": "insufficient context"},
            "ungrounded": {"grounded": False, "refusal": False, "citations": []},
        }.get(self.scenario, {"grounded": True, "refusal": False, "citations": ["chunk-1"]})

        payload = {
            "answer": answer,
            "grounded": behavior["grounded"],
            "citations": behavior["citations"],
            "refusal": behavior["refusal"],
            "refusal_reason": behavior.get("refusal_reason"),
        }
        return json.dumps(payload)
