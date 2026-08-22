"""Unit tests for the 3 chunking strategies."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.retrieval.chunker import (
    FixedSizeChunker,
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


def test_semantic_chunker_keeps_sentences_whole():
    chunker = SemanticChunker(max_chunk_chars=60, sentence_overlap=0)
    chunks = chunker.chunk(SAMPLE_TEXT)
    assert len(chunks) > 1
    for c in chunks:
        assert c.strip().endswith((".", "!", "?"))


def test_metadata_aware_chunker_delegates():
    chunker = MetadataAwareChunker(base_chunker=SemanticChunker(max_chunk_chars=1000))
    chunks = chunker.chunk(SAMPLE_TEXT)
    assert len(chunks) >= 1


def test_get_chunker_factory_rejects_unknown_strategy():
    try:
        get_chunker("nonexistent_strategy")
        assert False, "should have raised ValueError"
    except ValueError:
        pass


def test_chunk_document_produces_chunk_records_with_correct_fields():
    records = chunk_document("doc-1", SAMPLE_TEXT, strategy="semantic")
    assert len(records) >= 1
    for r in records:
        assert r.document_id == "doc-1"
        assert r.strategy == "semantic"
        assert r.chunk_id
        assert r.text