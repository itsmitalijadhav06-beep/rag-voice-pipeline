"""
Retrieval Package supporting vast chunking strategies (Fixed, Sentence, Metadata-aware) and Vector Index interfaces.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.schemas import DocumentRecord, ChunkRecord, ContextChunk


class BaseChunker(ABC):
    """Abstract Base Class for Document Chunking Strategies."""

    @abstractmethod
    def chunk(self, document: DocumentRecord) -> List[ChunkRecord]:
        """Split a DocumentRecord into a list of ChunkRecord objects."""
        pass

    def chunk_batch(self, documents: List[DocumentRecord]) -> List[ChunkRecord]:
        """Convenience method to chunk a batch of DocumentRecords."""
        all_chunks: List[ChunkRecord] = []
        for doc in documents:
            all_chunks.extend(self.chunk(doc))
        return all_chunks


class BaseVectorStore(ABC):
    """Abstract Base Class for Vector DB Operations."""

    @abstractmethod
    def search(self, query_embedding: List[float], top_k: int = 3) -> List[ContextChunk]:
        """Perform vector search for nearest neighbor context chunks."""
        pass
