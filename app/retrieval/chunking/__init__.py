"""
Chunking package exposing strategy implementations and factory function.
"""

from typing import Optional
from app.retrieval import BaseChunker
from app.retrieval.chunking.fixed_overlap import FixedOverlapChunker
from app.retrieval.chunking.sentence import SentenceChunker
from app.retrieval.chunking.metadata_aware import PassageMetadataChunker


def get_chunker(strategy_name: str = "fixed_overlap", **kwargs) -> BaseChunker:
    """
    Factory function to retrieve configured Chunker instance.
    Supported strategies: fixed (fixed_overlap), sentence, metadata (passage_metadata).
    """
    strat = strategy_name.lower().strip()
    if strat in ("fixed", "fixed_overlap"):
        return FixedOverlapChunker(**kwargs)
    elif strat in ("sentence", "sentence_aware"):
        return SentenceChunker(**kwargs)
    elif strat in ("metadata", "passage_metadata", "structure"):
        return PassageMetadataChunker(**kwargs)
    else:
        raise ValueError(
            f"Unknown chunking strategy '{strategy_name}'. "
            f"Supported strategies: fixed_overlap, sentence, passage_metadata."
        )


__all__ = [
    "BaseChunker",
    "FixedOverlapChunker",
    "SentenceChunker",
    "PassageMetadataChunker",
    "get_chunker",
]
