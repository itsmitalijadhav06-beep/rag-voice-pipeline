"""
Phase 3D — Stable retrieval contract.

This is THE function Member 2's generate() calls. Do not change this
signature or return type without telling them — it's the integration point
between retrieval and generation.

    retrieve(query: str, top_k: int = 5) -> list[RetrievedChunk]

RetrievedChunk fields: chunk_id, document_id, text, score, metadata.
"""

from typing import List, Optional

from app.retrieval.pipeline import RetrievalPipeline
from app.retrieval.records import RetrievedChunk

# One shared pipeline instance for the whole process — indices are loaded
# lazily from disk (data/index/) on first use per strategy, not rebuilt.
_pipeline: Optional[RetrievalPipeline] = None


def _get_pipeline() -> RetrievalPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = RetrievalPipeline()
    return _pipeline


def retrieve(query: str, top_k: int = 5, strategy: str = "fixed") -> List[RetrievedChunk]:
    """Stable retrieval entry point.

    Args:
        query: the user's question (transcribed text string).
        top_k: how many chunks to return (default: 5).
        strategy: which pre-built chunking strategy's index to search
                  ("fixed" | "sentence" | "semantic"). Defaults to "fixed".

    Returns:
        List[RetrievedChunk] — empty list if nothing relevant is found.
        Raises RetrievalError (see app.core.exceptions) on hard failures.
    """
    if top_k <= 0:
        raise ValueError("top_k must be a positive integer > 0")
    if not query or not query.strip():
        return []

    pipeline = _get_pipeline()
    chunks, _latency_ms = pipeline.retrieve(query, strategy=strategy, top_k=top_k)
    return chunks


def retrieve_with_latency(query: str, top_k: int = 5, strategy: str = "fixed"):
    """Same as retrieve(), but also returns latency_ms — used by benchmark scripts."""
    if top_k <= 0:
        raise ValueError("top_k must be a positive integer > 0")
    if not query or not query.strip():
        return [], 0.0

    pipeline = _get_pipeline()
    return pipeline.retrieve(query, strategy=strategy, top_k=top_k)