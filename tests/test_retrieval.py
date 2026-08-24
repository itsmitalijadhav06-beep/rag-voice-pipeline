"""
Unit & Integration tests for Phase 3D retrieval contract.
"""

import pytest
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.exceptions import RetrievalError
from app.retrieval.records import RetrievedChunk
from app.retrieval.retrieve import retrieve, retrieve_with_latency


@pytest.fixture(scope="module", autouse=True)
def setup_temp_indexes(tmp_path_factory):
    # 1. Create a temporary directory for indexes
    temp_dir = tmp_path_factory.mktemp("test_indexes")
    
    # 2. Patch INDEX_DIR in app.retrieval.vector_store
    import app.retrieval.vector_store
    original_index_dir = app.retrieval.vector_store.INDEX_DIR
    app.retrieval.vector_store.INDEX_DIR = temp_dir
    
    # 3. Create a RetrievalPipeline with HashingEmbedder to avoid loading PyTorch / HF model
    from app.retrieval.embedder import HashingEmbedder
    from app.retrieval.pipeline import RetrievalPipeline
    import app.retrieval.retrieve
    
    test_embedder = HashingEmbedder(dim=384)
    test_pipeline = RetrievalPipeline(embedder=test_embedder)
    
    # Save original pipeline and set the test pipeline
    original_pipeline = app.retrieval.retrieve._pipeline
    app.retrieval.retrieve._pipeline = test_pipeline
    
    # 4. Build dummy documents and index them
    class DummyDocument:
        def __init__(self, doc_id: str, text: str, metadata: dict = None):
            self.document_id = doc_id
            self.text = text
            self.metadata = metadata or {}
            
    documents_data = {
        "en": [
            "A corporation is a legal entity created by state law.",
            "The weather is very nice today."
        ],
        "hi": [
            "कॉर्पोरेशन राज्य कानून द्वारा बनाई गई एक कानूनी इकाई है।",
            "आज मौसम बहुत अच्छा है।"
        ],
        "mr": [
            "कॉर्पोरेशन हा राज्य कायद्याद्वारे तयार केलेला एक कायदेशीर घटक आहे.",
            "आज हवामान खूप छान आहे।"
        ]
    }
    
    for lang, texts in documents_data.items():
        docs = [DummyDocument(f"doc-{lang}-{i}", text, {"language": lang}) for i, text in enumerate(texts)]
        # Build index for fixed, sentence, and semantic strategies
        test_pipeline.build_index(
            docs,
            strategies=["fixed", "sentence", "semantic"],
            language=lang
        )
        
    yield
    
    # Clean up and restore globals
    app.retrieval.vector_store.INDEX_DIR = original_index_dir
    app.retrieval.retrieve._pipeline = original_pipeline


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
    for chunk in chunks:
        assert isinstance(chunk, RetrievedChunk)
        assert chunk.chunk_id
        assert chunk.document_id
        assert isinstance(chunk.text, str)
        assert isinstance(chunk.score, float)
        assert "strategy_used" in chunk.metadata
        assert chunk.metadata["strategy_used"] == "sentence"


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


def test_retrieve_specific_combinations():
    # 1. fixed + en
    results = retrieve("What is a corporation?", top_k=1, strategy="fixed", language="en")
    assert len(results) > 0
    assert "en" in results[0].document_id

    # 2. fixed + hi
    results = retrieve("कॉर्पोरेशन क्या है?", top_k=1, strategy="fixed", language="hi")
    assert len(results) > 0
    assert "hi" in results[0].document_id

    # 3. fixed + mr
    results = retrieve("कॉर्पोरेशन काय आहे?", top_k=1, strategy="fixed", language="mr")
    assert len(results) > 0
    assert "mr" in results[0].document_id

    # 4. sentence + hi using temp fixture
    results = retrieve("मौसम क्या है?", top_k=1, strategy="sentence", language="hi")
    assert len(results) > 0
    assert results[0].metadata["strategy_used"] == "sentence"

    # 5. semantic + hi using temp fixture
    results = retrieve("मौसम क्या है?", top_k=1, strategy="semantic", language="hi")
    assert len(results) > 0
    assert results[0].metadata["strategy_used"] == "semantic"


def test_retrieve_missing_index_raises_retrieval_error(tmp_path):
    # 6. missing language/strategy index
    import app.retrieval.vector_store
    original_index_dir = app.retrieval.vector_store.INDEX_DIR
    app.retrieval.vector_store.INDEX_DIR = tmp_path
    
    from app.retrieval.pipeline import RetrievalPipeline
    import app.retrieval.retrieve
    original_pipeline = app.retrieval.retrieve._pipeline
    empty_pipeline = RetrievalPipeline(embedder=original_pipeline.embedder if original_pipeline else None)
    app.retrieval.retrieve._pipeline = empty_pipeline
    
    try:
        # Request strategy/language on an empty folder (missing index)
        with pytest.raises(RetrievalError) as exc_info:
            retrieve("What is a corporation?", strategy="fixed", language="en")
        assert "No saved index found for strategy 'fixed' and language 'en'" in str(exc_info.value)
        
        # Test language=unknown/missing
        # Since 'unknown' is not a valid language code, it falls back to text-based detection (English)
        with pytest.raises(RetrievalError) as exc_info:
            retrieve("What is a corporation?", strategy="fixed", language="unknown")
        assert "No saved index found for strategy 'fixed' and language 'en'" in str(exc_info.value)

        # Test valid language code but index is missing (mr)
        with pytest.raises(RetrievalError) as exc_info:
            retrieve("What is a corporation?", strategy="fixed", language="mr")
        assert "No saved index found for strategy 'fixed' and language 'mr'" in str(exc_info.value)

        # Test ambiguous Devanagari query without explicit language signal raises cannot determine language error
        with pytest.raises(RetrievalError) as exc_info:
            retrieve("कॉर्पोरेशन", strategy="fixed", language="unknown")
        assert "Cannot determine query language between Hindi and Marathi" in str(exc_info.value)
    finally:
        app.retrieval.vector_store.INDEX_DIR = original_index_dir
        app.retrieval.retrieve._pipeline = original_pipeline


def test_retrieve_invalid_strategy_raises_retrieval_error():
    # 7. invalid strategy
    import app.retrieval.retrieve
    from app.retrieval.pipeline import RetrievalPipeline
    original_pipeline = app.retrieval.retrieve._pipeline
    empty_pipeline = RetrievalPipeline(embedder=original_pipeline.embedder if original_pipeline else None)
    app.retrieval.retrieve._pipeline = empty_pipeline
    
    try:
        with pytest.raises(RetrievalError) as exc_info:
            retrieve("What is a corporation?", strategy="invalid_strategy", language="en")
        assert "No saved index found for strategy 'invalid_strategy'" in str(exc_info.value)
    finally:
        app.retrieval.retrieve._pipeline = original_pipeline


def test_retrieve_explicit_language_override():
    # 8. explicit language override
    # Query is Hindi "मौसम क्या है?", but we override with language="en"
    # It should look up english index and return English documents.
    results = retrieve("मौसम क्या है?", top_k=1, strategy="fixed", language="en")
    assert len(results) > 0
    assert "en" in results[0].document_id


def test_retrieve_automatic_language_detection():
    # 9. automatic language detection
    # Latin text -> "en"
    from app.retrieval.retrieve import resolve_query_language
    assert resolve_query_language("What is the weather today?") == "en"
    
    # Devanagari text with Hindi marker "है" -> "hi"
    assert resolve_query_language("आज का मौसम कैसा है?") == "hi"
    
    # Devanagari text with Marathi marker "आहे" -> "mr"
    assert resolve_query_language("आजचे हवामान कसे आहे?") == "mr"


def test_retrieve_latency_measurement():
    # 10. latency measurement (using retrieve_with_latency and retrieve_with_breakdown)
    chunks, latency_ms = retrieve_with_latency("मौसम क्या है?", top_k=2, strategy="sentence", language="hi")
    assert isinstance(chunks, list)
    assert isinstance(latency_ms, float)
    assert latency_ms > 0.0

    from app.retrieval.retrieve import retrieve_with_breakdown
    results, embed_ms, search_ms = retrieve_with_breakdown("मौसम क्या है?", top_k=2, strategy="sentence", language="hi")
    assert isinstance(results, list)
    assert isinstance(embed_ms, float)
    assert isinstance(search_ms, float)
    assert embed_ms >= 0.0
    assert search_ms >= 0.0


def test_retrieve_legacy_fallback_1(tmp_path):
    # Tests Fallback 1: fallback to base_dir / strategy_name / meta.json when language index not found
    import app.retrieval.vector_store
    original_index_dir = app.retrieval.vector_store.INDEX_DIR
    app.retrieval.vector_store.INDEX_DIR = tmp_path
    
    try:
        from app.retrieval.embedder import HashingEmbedder
        from app.retrieval.pipeline import RetrievalPipeline
        
        test_embedder = HashingEmbedder(dim=384)
        test_pipeline = RetrievalPipeline(embedder=test_embedder)
        
        class DummyDocument:
            def __init__(self, doc_id: str, text: str):
                self.document_id = doc_id
                self.text = text
                
        # Build index in the legacy directory (language = None)
        test_pipeline.build_index([DummyDocument("doc-legacy", "Legacy text")], strategies=["fixed"], language=None)
        
        import app.retrieval.retrieve
        orig_p = app.retrieval.retrieve._pipeline
        app.retrieval.retrieve._pipeline = test_pipeline
        try:
            results = retrieve("कॉर्पोरेशन क्या है?", strategy="fixed", language="hi")
            assert len(results) > 0
            assert results[0].document_id == "doc-legacy"
        finally:
            app.retrieval.retrieve._pipeline = orig_p
    finally:
        app.retrieval.vector_store.INDEX_DIR = original_index_dir


def test_retrieve_legacy_fallback_2(tmp_path):
    # Tests Fallback 2: base_dir / strategy_name.meta.json when language & folder index not found
    import app.retrieval.vector_store
    original_index_dir = app.retrieval.vector_store.INDEX_DIR
    app.retrieval.vector_store.INDEX_DIR = tmp_path
    
    try:
        from app.retrieval.vector_store import FAISSVectorStore
        from app.retrieval.records import ChunkRecord
        import faiss
        import pickle
        import json
        
        # Create legacy root layout files manually
        store = FAISSVectorStore(strategy_name="fixed", dimension=384, language=None)
        chunks = [ChunkRecord(chunk_id="chk-1", document_id="doc-1", text="Legacy root layout", strategy="fixed")]
        embeddings = np.random.rand(1, 384).astype("float32")
        store.build(chunks, embeddings)
        
        faiss.write_index(store._index, str(tmp_path / "fixed.faiss"))
        with open(tmp_path / "fixed.chunks.pkl", "wb") as f:
            pickle.dump(store._chunks, f)
        with open(tmp_path / "fixed.meta.json", "w", encoding="utf-8") as f:
            json.dump({
                "strategy_name": "fixed",
                "dimension": 384,
                "count": 1,
                "language": None
            }, f)
            
        loaded_store = FAISSVectorStore.load("fixed", language="hi")
        assert loaded_store.strategy_name == "fixed"
        assert len(loaded_store._chunks) == 1
        assert loaded_store._chunks[0].text == "Legacy root layout"
    finally:
        app.retrieval.vector_store.INDEX_DIR = original_index_dir
