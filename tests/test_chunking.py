"""Unit tests for Phase 3B chunking strategies."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.retrieval.chunker import (
    FixedSizeChunker,
    SentenceAwareChunker,
    SemanticChunker,
    MetadataAwareChunker,
    chunk_document,
    get_chunker,
)

SAMPLE_TEXT = (
    "This is the first sentence. This is the second sentence! "
    "Is this the third sentence? Yes, this is the fourth one. "
    "And here comes a fifth sentence for good measure."
)


def test_fixed_size_chunker_respects_overlap():
    chunker = FixedSizeChunker(chunk_size_words=10, overlap_words=3)
    chunks = chunker.chunk(SAMPLE_TEXT)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c.split()) <= 10


def test_fixed_size_chunker_validates_overlap():
    with pytest.raises(ValueError):
        FixedSizeChunker(chunk_size_words=10, overlap_words=10)


def test_sentence_aware_chunker_keeps_sentences_whole():
    chunker = SentenceAwareChunker(max_chunk_chars=60, sentence_overlap=0)
    chunks = chunker.chunk(SAMPLE_TEXT)
    assert len(chunks) > 1
    for c in chunks:
        assert c.strip().endswith((".", "!", "?", "।"))


def test_semantic_chunker_groups_sentences():
    chunker = SemanticChunker(similarity_threshold=0.5, max_chunk_sentences=2)
    chunks = chunker.chunk(SAMPLE_TEXT)
    assert len(chunks) >= 2


def test_metadata_aware_chunker_delegates():
    chunker = MetadataAwareChunker(base_chunker=SentenceAwareChunker(max_chunk_chars=1000))
    chunks = chunker.chunk(SAMPLE_TEXT)
    assert len(chunks) >= 1


def test_get_chunker_factory_rejects_unknown_strategy():
    with pytest.raises(ValueError):
        get_chunker("nonexistent_strategy")


def test_chunk_document_produces_chunk_records_with_metadata():
    doc_meta = {"query_id": "123", "language": "hi", "source": "msmarco"}
    records = chunk_document("doc-1", SAMPLE_TEXT, strategy="fixed", doc_metadata=doc_meta)
    assert len(records) >= 1
    for r in records:
        assert r.document_id == "doc-1"
        assert r.strategy == "fixed"
        assert r.chunk_id.startswith("doc-1_chk_")
        assert r.text
        assert r.metadata["query_id"] == "123"
        assert r.metadata["language"] == "hi"
        assert "chunk_index" in r.metadata
        assert "total_chunks" in r.metadata