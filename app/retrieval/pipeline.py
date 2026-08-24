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

DEFAULT_STRATEGIES = ["fixed", "sentence", "semantic"]


def _get_store_key(strategy: str, language: Optional[str] = None) -> str:
    if not language:
        return strategy
    return f"{strategy}:{language.lower()}"


class RetrievalPipeline:
    """Owns one FAISS store per chunking strategy and a shared embedder."""

    def __init__(self, embedder: Optional[BaseEmbedder] = None):
        self.embedder = embedder or get_embedder()
        self.stores: Dict[str, FAISSVectorStore] = {}

    def build_index(
        self,
        documents: List,
        strategies: Optional[List[str]] = None,
        language: str = "mr",
        dataset: str = "MSMARCO-XI",
        split: str = "validation",
        limit: int = 500,
    ) -> None:
        """documents: list of DocumentRecord (from dataset.py)."""
        strategies = strategies or DEFAULT_STRATEGIES

        for strategy in strategies:
            all_chunks: List[ChunkRecord] = []
            for doc in documents:
                meta = getattr(doc, "metadata", {})
                all_chunks.extend(
                    chunk_document(doc.document_id, doc.text, strategy=strategy, doc_metadata=meta)
                )

            if not all_chunks:
                logger.warning(f"[{strategy}] No chunks produced from corpus — skipping index.")
                continue

            texts = [c.text for c in all_chunks]
            embeddings = self.embedder.embed(texts)

            store = FAISSVectorStore(
                strategy_name=strategy,
                dimension=self.embedder.dimension,
                language=language
            )
            store.dataset = dataset
            store.split = split
            store.limit = limit

            store.build(all_chunks, embeddings)
            store.save()
            key = _get_store_key(strategy, language)
            self.stores[key] = store

    def load_index(self, strategy: str, language: Optional[str] = None) -> None:
        key = _get_store_key(strategy, language)
        logger.info("[QUERY] pipeline.load_index: loading vector store for strategy=%s, language=%s", strategy, language)
        self.stores[key] = FAISSVectorStore.load(strategy, language=language)
        logger.info("[QUERY] pipeline.load_index: successfully loaded store for strategy=%s, language=%s (cached as key='%s')", strategy, language, key)

    def retrieve(self, query: str, strategy: str = "semantic", top_k: int = 5, language: Optional[str] = None):
        """Returns (chunks: list[RetrievedChunk], latency_ms: float)."""
        start = time.perf_counter()
        try:
            key = _get_store_key(strategy, language)
            if key not in self.stores:
                self.load_index(strategy, language)
            store = self.stores[key]
            query_embedding = self.embedder.embed([query])[0]
            results = store.search(query_embedding, top_k=top_k)
        except RetrievalError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise RetrievalError(f"Retrieval failed for strategy '{strategy}' and language '{language}': {exc}") from exc
        latency_ms = (time.perf_counter() - start) * 1000
        return results, latency_ms