"""
FAISS Vector Store (Phase 3C).

One index is built per chunking strategy so retrieval quality can be compared
strategy-vs-strategy (Phase 3D). Indices persist to disk under data/index/.
Stores ChunkRecord objects; search() returns RetrievedChunk objects — the
exact contract shape Member 2's generate() consumes.
"""

import json
import pickle
from pathlib import Path
from typing import List, Optional

import faiss
import numpy as np

from app.core.exceptions import RetrievalError
from app.core.logging import logger
from app.retrieval import BaseVectorStore
from app.retrieval.records import ChunkRecord, RetrievedChunk

INDEX_DIR = Path(__file__).resolve().parents[2] / "data" / "index"


class FAISSVectorStore(BaseVectorStore):
    """Flat inner-product FAISS index (embeddings are pre-normalized, so
    inner product == cosine similarity) plus a parallel list of ChunkRecord
    metadata keyed by row position."""

    def __init__(self, strategy_name: str, dimension: int, language: Optional[str] = None):
        self.strategy_name = strategy_name
        self.dimension = dimension
        self.language = language.lower() if language else None
        self._index = faiss.IndexFlatIP(dimension)
        self._chunks: List[ChunkRecord] = []
        self.dataset = "MSMARCO-XI"
        self.split = "validation"
        self.limit = 500

    def build(self, chunks: List[ChunkRecord], embeddings: np.ndarray) -> None:
        if len(chunks) != embeddings.shape[0]:
            raise RetrievalError("Chunk count and embedding count mismatch during index build.")
        if embeddings.shape[1] != self.dimension:
            raise RetrievalError(
                f"Embedding dimension {embeddings.shape[1]} != index dimension {self.dimension}."
            )
        self._index.add(embeddings.astype("float32"))
        self._chunks.extend(chunks)
        logger.info(
            f"[{self.strategy_name}] FAISS index built: {len(self._chunks)} chunks, dim={self.dimension}."
        )

    def search(self, query_embedding, top_k: int = 5) -> List[RetrievedChunk]:
        if self._index.ntotal == 0:
            raise RetrievalError(f"FAISS index for strategy '{self.strategy_name}' is empty.")
        import time
        logger.info("[QUERY] FAISSVectorStore.search: query shape=%s, index ntotal=%d", np.asarray(query_embedding).shape, self._index.ntotal)
        search_start = time.perf_counter()
        query = np.asarray(query_embedding, dtype="float32").reshape(1, -1)
        top_k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(query, top_k)
        logger.info("[QUERY] FAISSVectorStore.search: search call complete in %.2f ms", (time.perf_counter() - search_start) * 1000)

        results: List[RetrievedChunk] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            source = self._chunks[idx]
            results.append(
                RetrievedChunk(
                    chunk_id=source.chunk_id,
                    document_id=source.document_id,
                    text=source.text,
                    score=float(score),
                    metadata={**source.metadata, "strategy_used": self.strategy_name},
                )
            )
        return results

    def save(self, directory: Optional[Path] = None) -> Path:
        base_dir = directory or INDEX_DIR
        if self.language:
            strategy_dir = base_dir / self.language / self.strategy_name
        else:
            strategy_dir = base_dir / self.strategy_name
        strategy_dir.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self._index, str(strategy_dir / "index.faiss"))
        with open(strategy_dir / "chunks.pkl", "wb") as f:
            pickle.dump(self._chunks, f)
        with open(strategy_dir / "meta.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "strategy_name": self.strategy_name,
                    "dimension": self.dimension,
                    "count": len(self._chunks),
                    "language": self.language,
                    "dataset": self.dataset,
                    "split": self.split,
                    "limit": self.limit,
                },
                f,
                indent=2,
            )
        logger.info(f"[{self.strategy_name}] FAISS index saved to {strategy_dir}")
        return strategy_dir

    @classmethod
    def load(cls, strategy_name: str, directory: Optional[Path] = None, language: Optional[str] = None) -> "FAISSVectorStore":
        import time
        logger.info("[QUERY] FAISSVectorStore.load: loading index for strategy=%s, language=%s", strategy_name, language)
        load_start = time.perf_counter()
        base_dir = directory or INDEX_DIR
        strategy_dir = base_dir / language / strategy_name if language else base_dir / strategy_name

        meta_path = strategy_dir / "meta.json"
        faiss_path = strategy_dir / "index.faiss"
        chunks_path = strategy_dir / "chunks.pkl"

        # Fallback 1: If language is provided but directory is not found, fallback to legacy strategy_dir
        if language and not meta_path.exists():
            fallback_dir = base_dir / strategy_name
            if (fallback_dir / "meta.json").exists():
                logger.warning(
                    f"Index for language '{language}' not found at {strategy_dir}. "
                    f"Falling back to legacy layout at {fallback_dir}."
                )
                strategy_dir = fallback_dir
                meta_path = strategy_dir / "meta.json"
                faiss_path = strategy_dir / "index.faiss"
                chunks_path = strategy_dir / "chunks.pkl"

        # Fallback 2: Check legacy root index_dir if legacy file layout is present
        if not meta_path.exists():
            legacy_meta = base_dir / f"{strategy_name}.meta.json"
            if legacy_meta.exists():
                meta_path = legacy_meta
                faiss_path = base_dir / f"{strategy_name}.faiss"
                chunks_path = base_dir / f"{strategy_name}.chunks.pkl"
            else:
                raise RetrievalError(
                    f"No saved index found for strategy '{strategy_name}' and language '{language}' in {strategy_dir} or {base_dir}."
                )

        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)

        loaded_language = meta.get("language") or language
        store = cls(strategy_name=strategy_name, dimension=meta["dimension"], language=loaded_language)
        store.dataset = meta.get("dataset", "MSMARCO-XI")
        store.split = meta.get("split", "validation")
        store.limit = meta.get("limit", 500)

        store._index = faiss.read_index(str(faiss_path))
        with open(chunks_path, "rb") as f:
            store._chunks = pickle.load(f)

        logger.info(
            f"[{strategy_name}] FAISS index loaded ({len(store._chunks)} chunks, "
            f"dim={store.dimension}, lang={loaded_language}) in {(time.perf_counter() - load_start) * 1000:.2f} ms."
        )
        return store