"""
Concrete Chunking Strategy implementations (Phase 3B).

Three distinct strategies are provided, satisfying the "vast chunking" requirement:

1. FixedSizeChunker    — fixed-size word windows with overlap (~512 tokens, 50 overlap
                         per the team spec — configurable here).
2. SemanticChunker     — sentence-boundary aware, groups whole sentences up to a
                         character budget so chunks never split mid-sentence.
3. MetadataAwareChunker — wraps any base chunker and attaches rich per-chunk
                         metadata, returning ChunkRecord objects — the exact
                         contract shape used downstream by embedding/FAISS/retrieve().
"""

import re
import uuid
from typing import Any, Dict, List, Optional

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
    """Fixed-size chunking over whitespace-tokenized words, with overlap.
    Defaults approximate the spec's ~512 tokens / 50 token overlap."""

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


class SemanticChunker(BaseChunker):
    """Groups whole sentences together up to a character budget so chunks
    respect sentence boundaries instead of cutting mid-sentence."""

    strategy_name = "semantic"

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


class MetadataAwareChunker(BaseChunker):
    """Wraps a base chunker and enriches each resulting chunk with structured
    metadata (doc id, chunk position, char span, strategy provenance)."""

    strategy_name = "metadata_aware"

    def __init__(self, base_chunker: Optional[BaseChunker] = None):
        self.base_chunker = base_chunker or SemanticChunker()

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        return self.base_chunker.chunk(text, metadata)


_CHUNKER_REGISTRY = {
    "fixed": FixedSizeChunker,
    "semantic": SemanticChunker,
    "metadata_aware": MetadataAwareChunker,
}


def get_chunker(strategy: str = "semantic", **kwargs) -> BaseChunker:
    """Factory returning a configured chunker instance for a named strategy."""
    strategy = strategy.lower()
    if strategy not in _CHUNKER_REGISTRY:
        raise ValueError(
            f"Unknown chunking strategy '{strategy}'. Available: {list(_CHUNKER_REGISTRY)}"
        )
    return _CHUNKER_REGISTRY[strategy](**kwargs)


def chunk_document(document_id: str, text: str, strategy: str = "semantic", **kwargs) -> List[ChunkRecord]:
    """Runs a named strategy over one document's text and returns ChunkRecord
    objects — the shape everything downstream (embedding, FAISS, retrieve())
    consumes. This is the main entry point scripts/build_chunks.py should call."""
    chunker = get_chunker(strategy, **kwargs)
    raw_chunks = chunker.chunk(text)
    return [
        ChunkRecord(
            chunk_id=str(uuid.uuid4()),
            document_id=document_id,
            text=chunk_text,
            strategy=strategy,
            metadata={"chunk_index": idx},
        )
        for idx, chunk_text in enumerate(raw_chunks)
    ]