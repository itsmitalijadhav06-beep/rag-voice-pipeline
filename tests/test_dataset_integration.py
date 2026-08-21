"""
Dataset Integration Test for ai4bharat/MSMARCO-XI ingestion and chunking.
"""

import os
import pytest
from app.retrieval.ingestion import load_msmarco_dataset
from app.retrieval.chunking import get_chunker


@pytest.mark.anyio
@pytest.mark.skipif(
    os.getenv("SKIP_DATASET_INTEGRATION", "false").lower() == "true",
    reason="SKIP_DATASET_INTEGRATION is set to true",
)
async def test_msmarco_xi_dataset_ingestion_and_chunking():
    """
    Integration test that ingests a tiny sample (5 query rows) of MSMARCO-XI dataset,
    normalizes to DocumentRecords, and verifies chunking strategies.
    """
    docs = load_msmarco_dataset(language="hin", split="validation", limit=5)
    assert len(docs) > 0, "Should load at least 1 document from MSMARCO-XI sample"

    doc = docs[0]
    assert doc.document_id.startswith("doc_")
    assert "query_id" in doc.metadata
    assert "language" in doc.metadata

    # Test fixed_overlap chunker on loaded dataset documents
    fixed_chunker = get_chunker("fixed_overlap", chunk_size=500, overlap=50)
    fixed_chunks = fixed_chunker.chunk_batch(docs)
    assert len(fixed_chunks) >= len(docs)

    # Test sentence chunker on loaded dataset documents
    sentence_chunker = get_chunker("sentence", max_chunk_size=500)
    sentence_chunks = sentence_chunker.chunk_batch(docs)
    assert len(sentence_chunks) >= len(docs)

    # Test passage metadata chunker
    meta_chunker = get_chunker("passage_metadata")
    meta_chunks = meta_chunker.chunk_batch(docs)
    assert len(meta_chunks) >= len(docs)
