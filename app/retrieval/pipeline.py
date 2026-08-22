"""
Retrieval Pipeline (Phases 3B-3D orchestration).

Builds one FAISS index per chunking strategy from a corpus of documents,
and exposes retrieve() used by both the API and benchmark scripts. Also
measures per-call latency so it plugs into the harness/analytics layers.
"""

import time
from typing import Dict, List, Optional

from app.core.exceptions import RetrievalError
from app.core.logging import logger
from app.retrieval.chunker import chunk_document
from app.retrieval.embedder import BaseEmbedder, get_embedder
from app.retrieval.records import ChunkRecord, RetrievedChunk
from app.retrieval.vector_store import FAISSVectorStore

DEFAULT_STRATEGIES = ["fixed", "semantic", "metadata_aware"]


class RetrievalPipeline:
    """Owns one FAISS store per chunking strategy and a shared embedder."""

    def __init__(self, embedder: Optional[BaseEmbedder] = None):
        self.embedder = embedder or get_embedder()
        self.stores: Dict[str, FAISSVectorStore] = {}

    def build_index(self, documents: List, strategies: Optional[List[str]] = None) -> None:
        """documents: list of DocumentRecord (from dataset.py)."""
        strategies = strategies or DEFAULT_STRATEGIES

        for strategy in strategies:
            all_chunks: List[ChunkRecord] = []
            for doc in documents:
                all_chunks.extend(chunk_document(doc.document_id, doc.text, strategy=strategy))

            if not all_chunks:
                logger.warning(f"[{strategy}] No chunks produced from corpus — skipping index.")
                continue

            texts = [c.text for c in all_chunks]
            embeddings = self.embedder.embed(texts)

            store = FAISSVectorStore(strategy_name=strategy, dimension=self.embedder.dimension)
            store.build(all_chunks, embeddings)
            store.save()
            self.stores[strategy] = store

    def load_index(self, strategy: str) -> None:
        self.stores[strategy] = FAISSVectorStore.load(strategy)

    def retrieve(self, query: str, strategy: str = "semantic", top_k: int = 5):
        """Returns (chunks: list[RetrievedChunk], latency_ms: float)."""
        start = time.perf_counter()
        try:
            if strategy not in self.stores:
                self.load_index(strategy)
            store = self.stores[strategy]
            query_embedding = self.embedder.embed([query])[0]
            results = store.search(query_embedding, top_k=top_k)
        except RetrievalError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise RetrievalError(f"Retrieval failed for strategy '{strategy}': {exc}") from exc
        latency_ms = (time.perf_counter() - start) * 1000
        return results, latency_ms