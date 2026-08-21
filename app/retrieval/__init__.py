"""
Retrieval Package supporting vast chunking strategies (Fixed, Semantic, Metadata-aware) and Vector Index interfaces.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.schemas import ContextChunk


class BaseChunker(ABC):
    """Abstract Base Class for Document Chunking Strategies."""

    @abstractmethod
    def chunk(self, text: str, metadata: Dict[str, Any] = None) -> List[str]:
        """Split text document into chunks based on specific strategy."""
        pass


class BaseVectorStore(ABC):
    """Abstract Base Class for Vector DB Operations."""

    @abstractmethod
    def search(self, query_embedding: List[float], top_k: int = 3) -> List[ContextChunk]:
        """Perform vector search for nearest neighbor context chunks."""
        pass
