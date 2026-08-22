"""
Embedding layer (Phase 3C, part 1).

Provides a pluggable BaseEmbedder so the retrieval pipeline is not hard-wired
to one model:

- SentenceTransformerEmbedder: the real, production embedder
  (settings.EMBEDDING_MODEL_NAME, e.g. multilingual MiniLM — suited to the
  Indic-language MSMARCO-XI dataset).
- HashingEmbedder: a dependency-free, deterministic fallback used automatically
  when the sentence-transformers model can't be downloaded (e.g. no network)
  so the rest of the pipeline is still fully exercisable without external calls.

get_embedder() tries the real model first and only falls back on failure,
logging clearly which one is active.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

import numpy as np

from app.core.config import settings
from app.core.logging import logger


class BaseEmbedder(ABC):
    name: str = "base"

    @abstractmethod
    def embed(self, texts: List[str]) -> np.ndarray:
        """Return an (N, D) float32 array of embeddings for the given texts."""
        raise NotImplementedError

    @property
    @abstractmethod
    def dimension(self) -> int:
        raise NotImplementedError


class SentenceTransformerEmbedder(BaseEmbedder):
    """Wraps sentence-transformers. Requires network access on first run to
    download the model (or a local HF cache)."""

    name = "sentence_transformer"

    def __init__(self, model_name: Optional[str] = None):
        from sentence_transformers import SentenceTransformer  # lazy import

        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self._model = SentenceTransformer(self.model_name)

    def embed(self, texts: List[str]) -> np.ndarray:
        vectors = self._model.encode(
            texts, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False
        )
        return vectors.astype("float32")

    @property
    def dimension(self) -> int:
        if hasattr(self._model, "get_embedding_dimension"):
            return int(self._model.get_embedding_dimension())
        return int(self._model.get_sentence_embedding_dimension())



class HashingEmbedder(BaseEmbedder):
    """Deterministic, offline, dependency-free embedder using the classic
    feature-hashing trick over word n-grams, followed by L2 normalization.

    NOT a substitute for a real semantic embedding model in production — it
    exists so the chunking/indexing/retrieval/harness/guardrail code can be
    built, unit-tested, and demoed end-to-end without needing network access
    to Hugging Face. Swap in SentenceTransformerEmbedder for real deployments.
    """

    name = "hashing_fallback"

    def __init__(self, dim: int = 384, ngram_range=(1, 2)):
        self.dim = dim
        self.ngram_range = ngram_range

    def _tokenize(self, text: str) -> List[str]:
        return text.lower().split()

    def _ngrams(self, tokens: List[str]) -> List[str]:
        grams = []
        for n in range(self.ngram_range[0], self.ngram_range[1] + 1):
            for i in range(len(tokens) - n + 1):
                grams.append(" ".join(tokens[i : i + n]))
        return grams or tokens

    def embed(self, texts: List[str]) -> np.ndarray:
        matrix = np.zeros((len(texts), self.dim), dtype="float32")
        for row, text in enumerate(texts):
            tokens = self._tokenize(text)
            for gram in self._ngrams(tokens):
                idx = hash(gram) % self.dim
                matrix[row, idx] += 1.0
            norm = np.linalg.norm(matrix[row])
            if norm > 0:
                matrix[row] /= norm
        return matrix

    @property
    def dimension(self) -> int:
        return self.dim


def get_embedder(prefer_real_model: bool = True) -> BaseEmbedder:
    """Returns the configured embedder, falling back to the offline hashing
    embedder if the real model can't be loaded (e.g. no network)."""
    if prefer_real_model:
        try:
            embedder = SentenceTransformerEmbedder()
            logger.info(f"Loaded embedding model '{embedder.model_name}'.")
            return embedder
        except Exception as exc:  # noqa: BLE001 — deliberately broad, network/import errors vary
            logger.warning(
                f"Falling back to offline HashingEmbedder — could not load "
                f"'{settings.EMBEDDING_MODEL_NAME}': {exc}"
            )
    return HashingEmbedder()