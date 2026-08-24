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

from app.core.exceptions import RetrievalError
from app.core.logging import logger
from app.retrieval.pipeline import RetrievalPipeline, _get_store_key
from app.retrieval.records import RetrievedChunk

# One shared pipeline instance for the whole process — indices are loaded
# lazily from disk (data/index/) on first use per strategy, not rebuilt.
_pipeline: Optional[RetrievalPipeline] = None


def _get_pipeline() -> RetrievalPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = RetrievalPipeline()
    return _pipeline


def normalize_language(lang_code: Optional[str]) -> str:
    """Normalize language code or name to en, hi, mr."""
    if not lang_code:
        return "en"
    clean = lang_code.strip().lower()
    if clean in ("en", "en-in", "english"):
        return "en"
    if clean in ("hi", "hi-in", "hindi"):
        return "hi"
    if clean in ("mr", "mr-in", "marathi"):
        return "mr"
    # Fallback to check prefix
    if clean.startswith("en"):
        return "en"
    if clean.startswith("hi"):
        return "hi"
    if clean.startswith("mr"):
        return "mr"
    return clean


def resolve_query_language(query: str, language_signal: Optional[str] = None) -> str:
    """Resolve and validate query language routing based on override, STT, or text heuristics."""
    # 1. Check explicit language override or STT language signal
    if language_signal:
        norm = normalize_language(language_signal)
        if norm in ("en", "hi", "mr"):
            return norm

    # 2. Text-based heuristic only when reliable
    if not query or not query.strip():
        return "en"

    # Latin text check (English)
    # Check if text contains primarily Latin alphabet letters
    latin_chars = sum(1 for char in query if ord(char) in range(65, 91) or ord(char) in range(97, 123))
    total_chars = sum(1 for char in query if char.isalnum())
    
    if total_chars > 0 and (latin_chars / total_chars) > 0.5:
        return "en"

    # Check for Devanagari characters (range 0900-097F)
    has_devanagari = any(ord(char) in range(0x0900, 0x0980) for char in query)
    if has_devanagari:
        # Detect Marathi markers
        marathi_markers = ["आहे", "आणि", "किंवा", "काय", "पण", "मला", "तुला", "आपण", "ळ", "उत्पादन", "माहिती", "नाव", "केला"]
        if "ळ" in query or any(word in query for word in marathi_markers):
            return "mr"
            
        # Detect Hindi markers
        hindi_markers = ["है", "हैं", "था", "थी", "थे", "कहा", "किया", "क्या", "निगम", "की", "का"]
        if any(word in query for word in hindi_markers):
            return "hi"
            
        # Devanagari text with no reliable marker
        raise RetrievalError(
            "Cannot determine query language between Hindi and Marathi for Devanagari text without an explicit language signal."
        )

    return "en"  # Default fallback


def retrieve(
    query: str, top_k: int = 5, strategy: str = "fixed", language: Optional[str] = None
) -> List[RetrievedChunk]:
    """Stable retrieval entry point.

    Args:
        query: the user's question (transcribed text string).
        top_k: how many chunks to return (default: 5).
        strategy: which pre-built chunking strategy's index to search
                  ("fixed" | "sentence" | "semantic"). Defaults to "fixed".
        language: optional language code override.

    Returns:
        List[RetrievedChunk] — empty list if nothing relevant is found.
        Raises RetrievalError (see app.core.exceptions) on hard failures.
    """
    if top_k <= 0:
        raise ValueError("top_k must be a positive integer > 0")
    if not query or not query.strip():
        return []

    resolved_lang = resolve_query_language(query, language)
    pipeline = _get_pipeline()
    chunks, _latency_ms = pipeline.retrieve(query, strategy=strategy, top_k=top_k, language=resolved_lang)
    return chunks


def retrieve_with_latency(
    query: str, top_k: int = 5, strategy: str = "fixed", language: Optional[str] = None
):
    """Same as retrieve(), but also returns latency_ms — used by benchmark scripts."""
    if top_k <= 0:
        raise ValueError("top_k must be a positive integer > 0")
    if not query or not query.strip():
        return [], 0.0

    resolved_lang = resolve_query_language(query, language)
    pipeline = _get_pipeline()
    return pipeline.retrieve(query, strategy=strategy, top_k=top_k, language=resolved_lang)


def retrieve_with_breakdown(
    query: str, top_k: int = 5, strategy: str = "fixed", language: Optional[str] = None
) -> tuple[List[RetrievedChunk], float, float]:
    """Retrieve chunks and return separate embedding and retrieval search latencies."""
    if top_k <= 0:
        raise ValueError("top_k must be a positive integer > 0")
    if not query or not query.strip():
        return [], 0.0, 0.0

    resolved_lang = resolve_query_language(query, language)
    logger.info("[QUERY] retrieve_with_breakdown: resolved language=%s", resolved_lang)
    
    pipe_start = time.perf_counter()
    pipeline = _get_pipeline()
    logger.info("[QUERY] retrieve_with_breakdown: pipeline fetched in %.2f ms", (time.perf_counter() - pipe_start) * 1000)
    
    key = _get_store_key(strategy, resolved_lang)
    if key not in pipeline.stores:
        logger.info("[QUERY] retrieve_with_breakdown: index '%s' not cached. Loading from disk.", key)
        load_start = time.perf_counter()
        pipeline.load_index(strategy, resolved_lang)
        logger.info("[QUERY] retrieve_with_breakdown: index '%s' loaded in %.2f ms", key, (time.perf_counter() - load_start) * 1000)
    store = pipeline.stores[key]

    logger.info("[QUERY] retrieve_with_breakdown: query embedding start")
    embed_start = time.perf_counter()
    query_embedding = pipeline.embedder.embed([query])[0]
    embedding_ms = (time.perf_counter() - embed_start) * 1000
    logger.info("[QUERY] retrieve_with_breakdown: query embedding complete (%.2f ms)", embedding_ms)

    logger.info("[QUERY] retrieve_with_breakdown: FAISS search start")
    search_start = time.perf_counter()
    results = store.search(query_embedding, top_k=top_k)
    retrieval_ms = (time.perf_counter() - search_start) * 1000
    logger.info("[QUERY] retrieve_with_breakdown: FAISS search complete (%.2f ms)", retrieval_ms)

    return results, embedding_ms, retrieval_ms