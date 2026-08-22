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

    def __init__(self, strategy_name: str, dimension: int):
        self.strategy_name = strategy_name
        self.dimension = dimension
        self._index = faiss.IndexFlatIP(dimension)
        self._chunks: List[ChunkRecord] = []

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
        query = np.asarray(query_embedding, dtype="float32").reshape(1, -1)
        top_k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(query, top_k)

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
                },
                f,
                indent=2,
            )
        logger.info(f"[{self.strategy_name}] FAISS index saved to {strategy_dir}")
        return strategy_dir

    @classmethod
    def load(cls, strategy_name: str, directory: Optional[Path] = None) -> "FAISSVectorStore":
        base_dir = directory or INDEX_DIR
        strategy_dir = base_dir / strategy_name

        # Check strategy subdirectory first
        meta_path = strategy_dir / "meta.json"
        faiss_path = strategy_dir / "index.faiss"
        chunks_path = strategy_dir / "chunks.pkl"

        # Fallback to root index_dir if legacy file layout is present
        if not meta_path.exists():
            legacy_meta = base_dir / f"{strategy_name}.meta.json"
            if legacy_meta.exists():
                meta_path = legacy_meta
                faiss_path = base_dir / f"{strategy_name}.faiss"
                chunks_path = base_dir / f"{strategy_name}.chunks.pkl"
            else:
                raise RetrievalError(
                    f"No saved index found for strategy '{strategy_name}' in {strategy_dir} or {base_dir}."
                )

        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)

        store = cls(strategy_name=strategy_name, dimension=meta["dimension"])
        store._index = faiss.read_index(str(faiss_path))
        with open(chunks_path, "rb") as f:
            store._chunks = pickle.load(f)

        logger.info(f"[{strategy_name}] FAISS index loaded ({len(store._chunks)} chunks, dim={store.dimension}).")
        return store