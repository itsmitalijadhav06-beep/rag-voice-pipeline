"""
Custom Exception hierarchy for Voice-Enabled RAG Pipeline.
"""


class BaseRAGException(Exception):
    """Base exception for all RAG pipeline errors."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class STTProcessingError(BaseRAGException):
    """Raised when speech-to-text processing fails."""

    def __init__(self, message: str = "Speech-to-text processing failed."):
        super().__init__(message, status_code=502)


class RetrievalError(BaseRAGException):
    """Raised when vector DB search or document retrieval fails."""

    def __init__(self, message: str = "Context retrieval failed."):
        super().__init__(message, status_code=500)


class GenerationError(BaseRAGException):
    """Raised when LLM synthesis or answer generation fails."""

    def __init__(self, message: str = "Answer generation failed."):
        super().__init__(message, status_code=502)


class GuardrailViolation(BaseRAGException):
    """Raised when a query or response violates safety / groundedness guardrails."""

    def __init__(self, message: str = "Query or output violated guardrail policies."):
        super().__init__(message, status_code=400)


class SLAExceededWarning(BaseRAGException):
    """Raised/Logged when latency exceeds sub-200ms target."""

    def __init__(self, elapsed_ms: float):
        super().__init__(
            f"Latency SLA breached: Process took {elapsed_ms:.2f}ms (>200.0ms)",
            status_code=200,
        )
        self.elapsed_ms = elapsed_ms
