"""
Fixed-size overlap chunking strategy.
"""

import hashlib
from typing import List, Optional
from app.schemas import DocumentRecord, ChunkRecord
from app.retrieval import BaseChunker


class FixedOverlapChunker(BaseChunker):
    """
    Fixed-size chunking with configurable overlap.
    Supports character-level or token/word approximation.
    """

    def __init__(self, chunk_size: int = 1000, overlap: int = 150):
        """
        :param chunk_size: Target size of each chunk in characters (approx 200-300 words / tokens).
        :param overlap: Overlap size between consecutive chunks in characters.
        """
        if overlap >= chunk_size:
            raise ValueError(f"Overlap ({overlap}) must be strictly smaller than chunk_size ({chunk_size}).")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, document: DocumentRecord) -> List[ChunkRecord]:
        """Splits document text into fixed-size overlapping chunks."""
        text = document.text.strip() if document.text else ""
        if not text:
            return []

        doc_len = len(text)
        if doc_len <= self.chunk_size:
            # Document fits in a single chunk
            chunk_id = f"{document.document_id}_fixed_0"
            return [
                ChunkRecord(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    text=text,
                    strategy="fixed_overlap",
                    start_position=0,
                    end_position=doc_len,
                    metadata=dict(document.metadata),
                )
            ]

        chunks: List[ChunkRecord] = []
        step = self.chunk_size - self.overlap
        start = 0
        chunk_idx = 0

        while start < doc_len:
            end = min(start + self.chunk_size, doc_len)
            chunk_text = text[start:end]

            chunk_id = f"{document.document_id}_fixed_{chunk_idx}"
            chunks.append(
                ChunkRecord(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    text=chunk_text,
                    strategy="fixed_overlap",
                    start_position=start,
                    end_position=end,
                    metadata=dict(document.metadata),
                )
            )

            chunk_idx += 1
            if end == doc_len:
                break
            start += step

        return chunks
