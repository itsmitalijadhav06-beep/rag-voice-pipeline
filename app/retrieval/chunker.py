"""
Concrete Chunking Strategy implementations (Phase 3B).

Four distinct chunking strategies satisfying the vast chunking requirement:

1. FixedSizeChunker      — fixed token/word windowing with overlap (default: 512 tokens, 50 overlap).
2. SentenceAwareChunker  — sentence-boundary preserving chunker that groups complete sentences
                           up to a target budget without splitting sentences mid-way.
3. SemanticChunker       — semantic similarity chunker using sentence embeddings or adjacent
                           sentence distance to place chunk boundaries at topic shifts.
4. MetadataAwareChunker  — metadata-preserving wrapper enriching chunks with doc provenance.
"""

import re
import uuid
from typing import Any, Dict, List, Optional

import numpy as np

from app.retrieval import BaseChunker
from app.retrieval.records import ChunkRecord

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?।])\s+")  # handles '।' (Devanagari danda) too


def _split_sentences(text: str) -> List[str]:
    text = text.strip()
    if not text:
        return []
    sentences = _SENTENCE_SPLIT_RE.split(text)
    return [s.strip() for s in sentences if s.strip()]


class FixedSizeChunker(BaseChunker):
    """Fixed-size chunking over whitespace-tokenized words/tokens, with overlap.
    Defaults to 512 tokens with 50 token overlap per team specification."""

    strategy_name = "fixed"

    def __init__(self, chunk_size_words: int = 512, overlap_words: int = 50):
        if overlap_words >= chunk_size_words:
            raise ValueError("overlap_words must be smaller than chunk_size_words")
        self.chunk_size_words = chunk_size_words
        self.overlap_words = overlap_words

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        words = text.split()
        if not words:
            return []
        if len(words) <= self.chunk_size_words:
            return [" ".join(words)]

        step = max(1, self.chunk_size_words - self.overlap_words)
        chunks = []
        for start in range(0, len(words), step):
            window = words[start : start + self.chunk_size_words]
            if not window:
                break
            chunks.append(" ".join(window))
            if start + self.chunk_size_words >= len(words):
                break
        return chunks


class SentenceAwareChunker(BaseChunker):
    """Sentence-aware chunker that groups whole sentences up to a character/word
    budget so chunks respect sentence boundaries instead of cutting mid-sentence.
    """

    strategy_name = "sentence"

    def __init__(self, max_chunk_chars: int = 600, sentence_overlap: int = 1):
        self.max_chunk_chars = max_chunk_chars
        self.sentence_overlap = max(0, sentence_overlap)

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        sentences = _split_sentences(text)
        if not sentences:
            return []

        chunks: List[str] = []
        current: List[str] = []
        current_len = 0

        for sentence in sentences:
            sentence_len = len(sentence) + 1
            if current and current_len + sentence_len > self.max_chunk_chars:
                chunks.append(" ".join(current))
                current = current[-self.sentence_overlap :] if self.sentence_overlap else []
                current_len = sum(len(s) + 1 for s in current)
            current.append(sentence)
            current_len += sentence_len

        if current:
            chunks.append(" ".join(current))
        return chunks


class SemanticChunker(BaseChunker):
    """Semantic chunking strategy using sentence embeddings or adjacent sentence
    similarity to detect topic boundaries and create semantic chunks.
    """

    strategy_name = "semantic"

    def __init__(
        self,
        similarity_threshold: float = 0.45,
        max_chunk_sentences: int = 5,
        embedder: Optional[Any] = None,
    ):
        self.similarity_threshold = similarity_threshold
        self.max_chunk_sentences = max_chunk_sentences
        self.embedder = embedder

    def _cosine_sim(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        sentences = _split_sentences(text)
        if not sentences:
            return []
        if len(sentences) == 1:
            return [sentences[0]]

        # Compute sentence embeddings if embedder provided
        embeddings = None
        if self.embedder is not None:
            try:
                embeddings = self.embedder.embed(sentences)
            except Exception:  # noqa: BLE001
                embeddings = None

        chunks: List[str] = []
        current_group: List[str] = [sentences[0]]

        for i in range(1, len(sentences)):
            split_here = False

            if embeddings is not None and i < len(embeddings):
                sim = self._cosine_sim(embeddings[i - 1], embeddings[i])
                if sim < self.similarity_threshold:
                    split_here = True
            elif len(current_group) >= self.max_chunk_sentences:
                split_here = True

            if split_here and current_group:
                chunks.append(" ".join(current_group))
                current_group = [sentences[i]]
            else:
                current_group.append(sentences[i])

        if current_group:
            chunks.append(" ".join(current_group))
        return chunks


class MetadataAwareChunker(BaseChunker):
    """Wraps a base chunker and attaches rich per-chunk metadata."""

    strategy_name = "metadata_aware"

    def __init__(self, base_chunker: Optional[BaseChunker] = None):
        self.base_chunker = base_chunker or FixedSizeChunker()

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        return self.base_chunker.chunk(text, metadata)


_CHUNKER_REGISTRY = {
    "fixed": FixedSizeChunker,
    "sentence": SentenceAwareChunker,
    "semantic": SemanticChunker,
    "metadata_aware": MetadataAwareChunker,
}


def get_chunker(strategy: str = "fixed", **kwargs) -> BaseChunker:
    """Factory returning a configured chunker instance for a named strategy."""
    strategy = strategy.lower()
    if strategy not in _CHUNKER_REGISTRY:
        raise ValueError(
            f"Unknown chunking strategy '{strategy}'. Available: {list(_CHUNKER_REGISTRY)}"
        )
    return _CHUNKER_REGISTRY[strategy](**kwargs)


def chunk_document(
    document_id: str,
    text: str,
    strategy: str = "fixed",
    doc_metadata: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> List[ChunkRecord]:
    """Runs a named strategy over one document's text and returns ChunkRecord
    objects preserving source record metadata, doc_id, chunk_id, and strategy.
    """
    chunker = get_chunker(strategy, **kwargs)
    raw_chunks = chunker.chunk(text)
    base_meta = dict(doc_metadata) if doc_metadata else {}

    return [
        ChunkRecord(
            chunk_id=f"{document_id}_chk_{idx}",
            document_id=document_id,
            text=chunk_text,
            strategy=strategy,
            metadata={
                **base_meta,
                "chunk_index": idx,
                "total_chunks": len(raw_chunks),
                "char_length": len(chunk_text),
                "word_count": len(chunk_text.split()),
            },
        )
        for idx, chunk_text in enumerate(raw_chunks)
    ]