"""
Shared data structures for the retrieval pipeline (Phase 3B-3D contract).

These are the exact shapes Member 2's generation code depends on — do not
rename fields without telling them.
"""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class ChunkRecord:
    """A chunk produced by a chunking strategy, before embedding/indexing."""
    chunk_id: str
    document_id: str
    text: str
    strategy: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievedChunk:
    """What retrieve() returns — this is the stable contract Member 2 codes against."""
    chunk_id: str
    document_id: str
    text: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)