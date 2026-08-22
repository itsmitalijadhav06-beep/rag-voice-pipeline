"""
Phase 3D — Stable retrieval contract.

This is THE function Member 2's generate() calls. Do not change this
signature or return type without telling them — it's the integration point
between retrieval and generation.

    retrieve(query: str, top_k: int = 5) -> list[RetrievedChunk]

RetrievedChunk fields: chunk_id, document_id, text, score, metadata.
"""

import time
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


def retrieve_with_breakdown(
    query: str, top_k: int = 5, strategy: str = "fixed"
) -> tuple[List[RetrievedChunk], float, float]:
    """Retrieve chunks and return separate embedding and retrieval search latencies."""
    if top_k <= 0:
        raise ValueError("top_k must be a positive integer > 0")
    if not query or not query.strip():
        return [], 0.0, 0.0

    pipeline = _get_pipeline()
    if strategy not in pipeline.stores:
        pipeline.load_index(strategy)
    store = pipeline.stores[strategy]

    embed_start = time.perf_counter()
    query_embedding = pipeline.embedder.embed([query])[0]
    embedding_ms = (time.perf_counter() - embed_start) * 1000

    search_start = time.perf_counter()
    results = store.search(query_embedding, top_k=top_k)
    retrieval_ms = (time.perf_counter() - search_start) * 1000

    return results, embedding_ms, retrieval_ms