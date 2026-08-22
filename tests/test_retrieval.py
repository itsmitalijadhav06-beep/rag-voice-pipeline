"""
Unit & Integration tests for Phase 3D retrieval contract.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.exceptions import RetrievalError
from app.retrieval.records import RetrievedChunk
from app.retrieval.retrieve import retrieve, retrieve_with_latency


def test_retrieve_returns_retrieved_chunks():
    results = retrieve("कॉर्पोरेशन क्या है?", top_k=3, strategy="fixed")
    assert isinstance(results, list)
    assert len(results) <= 3
    for chunk in results:
        assert isinstance(chunk, RetrievedChunk)
        assert chunk.chunk_id
        assert chunk.document_id
        assert isinstance(chunk.text, str)
        assert isinstance(chunk.score, float)
        assert "strategy_used" in chunk.metadata


def test_retrieve_with_latency_returns_tuple():
    chunks, latency_ms = retrieve_with_latency("मौसम क्या है?", top_k=2, strategy="sentence")
    assert isinstance(chunks, list)
    assert isinstance(latency_ms, float)
    assert latency_ms > 0.0


def test_retrieve_empty_query_returns_empty_list():
    results = retrieve("", top_k=5)
    assert results == []

    results_spaces = retrieve("   ", top_k=5)
    assert results_spaces == []


def test_retrieve_invalid_top_k_raises_value_error():
    with pytest.raises(ValueError):
        retrieve("query", top_k=0)

    with pytest.raises(ValueError):
        retrieve("query", top_k=-5)


def test_retrieve_different_strategies():
    for strat in ["fixed", "sentence", "semantic"]:
        results = retrieve("विज्ञान क्या है?", top_k=3, strategy=strat)
        assert isinstance(results, list)
        if results:
            assert results[0].metadata["strategy_used"] == strat
