"""
Unit tests for Document Chunking Engine and strategies.
Fast unit tests using synthetic DocumentRecord fixtures (no network required).
"""

import pytest
import json
from app.schemas import DocumentRecord, ChunkRecord
from app.retrieval.chunking import get_chunker, FixedOverlapChunker, SentenceChunker, PassageMetadataChunker


@pytest.fixture
def sample_doc():
    return DocumentRecord(
        document_id="doc_test_100",
        text="This is sentence one. This is sentence two! Sentence three is longer and contains details. Sentence four concludes.",
        metadata={"query_id": 100, "source": "unit_test", "language": "en"},
    )


def test_empty_document():
    """1: Empty document text returns an empty list of chunks."""
    doc = DocumentRecord(document_id="doc_empty", text="", metadata={"query_id": 1})
    for strat in ["fixed_overlap", "sentence", "passage_metadata"]:
        chunker = get_chunker(strat)
        chunks = chunker.chunk(doc)
        assert chunks == []


def test_short_document(sample_doc):
    """2: Document shorter than target chunk size returns a single chunk."""
    chunker = FixedOverlapChunker(chunk_size=1000, overlap=100)
    chunks = chunker.chunk(sample_doc)
    assert len(chunks) == 1
    assert chunks[0].text == sample_doc.text
    assert chunks[0].start_position == 0
    assert chunks[0].end_position == len(sample_doc.text)


def test_fixed_size_chunking():
    """3: Fixed-size chunking splits large document into expected number of chunks."""
    large_text = "Word " * 300  # ~1500 chars
    doc = DocumentRecord(document_id="doc_large", text=large_text, metadata={"key": "val"})
    chunker = FixedOverlapChunker(chunk_size=500, overlap=100)
    chunks = chunker.chunk(doc)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c.text) <= 500
        assert c.strategy == "fixed_overlap"


def test_overlap_behavior():
    """4: Verifies overlap correctness in fixed overlap chunker."""
    text = "0123456789" * 10  # 100 chars
    doc = DocumentRecord(document_id="doc_overlap", text=text, metadata={})
    chunker = FixedOverlapChunker(chunk_size=40, overlap=10)
    chunks = chunker.chunk(doc)

    assert len(chunks) >= 3
    # Check that tail of chunk 0 overlaps with head of chunk 1
    overlap_len = 10
    tail_chunk0 = chunks[0].text[-overlap_len:]
    head_chunk1 = chunks[1].text[:overlap_len]
    assert tail_chunk0 == head_chunk1


def test_sentence_boundaries():
    """5: Sentence chunker preserves sentence integrity and does not split mid-sentence."""
    text = "First sentence here. Second sentence follows. Third sentence ends."
    doc = DocumentRecord(document_id="doc_sent", text=text, metadata={})
    chunker = SentenceChunker(max_chunk_size=45, sentence_overlap_count=0)
    chunks = chunker.chunk(doc)

    assert len(chunks) >= 2
    for c in chunks:
        assert c.strategy == "sentence"
        # Each chunk should end with a period or complete sentence
        assert c.text.endswith(".") or c.text.endswith("!") or c.text.endswith("?")


def test_metadata_preservation(sample_doc):
    """6: Verifies that original document metadata is preserved in generated chunks."""
    chunker = PassageMetadataChunker()
    chunks = chunker.chunk(sample_doc)
    assert len(chunks) > 0
    for c in chunks:
        assert c.metadata["query_id"] == 100
        assert c.metadata["source"] == "unit_test"
        assert c.metadata["language"] == "en"


def test_deterministic_chunk_ids(sample_doc):
    """7: Chunk IDs are deterministic for repeated chunker calls."""
    chunker = FixedOverlapChunker(chunk_size=50, overlap=10)
    run1 = [c.chunk_id for c in chunker.chunk(sample_doc)]
    run2 = [c.chunk_id for c in chunker.chunk(sample_doc)]
    assert run1 == run2
    assert run1[0] == "doc_test_100_fixed_0"


def test_chunking_factory():
    """8: get_chunker returns correct strategy instance and raises on invalid strategy."""
    c_fixed = get_chunker("fixed_overlap")
    assert isinstance(c_fixed, FixedOverlapChunker)

    c_sent = get_chunker("sentence")
    assert isinstance(c_sent, SentenceChunker)

    c_meta = get_chunker("passage_metadata")
    assert isinstance(c_meta, PassageMetadataChunker)

    with pytest.raises(ValueError) as exc_info:
        get_chunker("invalid_strategy_name")
    assert "Unknown chunking strategy" in str(exc_info.value)


def test_malformed_document_record():
    """9: Test error handling for missing/malformed DocumentRecord fields."""
    with pytest.raises(Exception):
        # Missing mandatory text field
        DocumentRecord(document_id="doc_bad")


def test_serialization_deserialization(sample_doc):
    """10: Verifies serialization and deserialization of DocumentRecord and ChunkRecord."""
    chunker = get_chunker("fixed_overlap")
    chunks = chunker.chunk(sample_doc)
    chunk = chunks[0]

    # JSON serialization
    json_str = chunk.model_dump_json()
    assert isinstance(json_str, str)

    # Deserialization
    restored = ChunkRecord.model_validate_json(json_str)
    assert restored.chunk_id == chunk.chunk_id
    assert restored.document_id == chunk.document_id
    assert restored.text == chunk.text
    assert restored.strategy == chunk.strategy
    assert restored.metadata == chunk.metadata
