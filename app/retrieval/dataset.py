"""
Dataset loading and normalization (Phase 3A).

Loads ai4bharat/MSMARCO-XI and converts rows into a normalized DocumentRecord
structure, so the rest of the pipeline (chunking, embedding) never has to
deal with the dataset's raw column names directly.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logging import logger

SAMPLE_CORPUS_PATH = Path(__file__).resolve().parents[2] / "data" / "raw" / "sample_corpus.jsonl"


@dataclass
class DocumentRecord:
    document_id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


def _find_text_field(row: dict) -> str:
    """MSMARCO-style datasets vary in field naming — try common candidates first."""
    for field_name in ("passage", "text", "context", "answer", "document"):
        if field_name in row and isinstance(row[field_name], str):
            return row[field_name]
    for value in row.values():
        if isinstance(value, str):
            return value
    return ""


def _find_id_field(row: dict, fallback_index: int) -> str:
    for field_name in ("id", "doc_id", "document_id", "passage_id", "pid"):
        if field_name in row:
            return str(row[field_name])
    return str(fallback_index)


def load_msmarco_xi(max_rows: int = 5000) -> List[DocumentRecord]:
    """Tries the real Hugging Face dataset first; falls back to a local
    sample corpus if it can't be downloaded (e.g. no internet access)."""
    try:
        from datasets import load_dataset

        logger.info("Attempting to load ai4bharat/MSMARCO-XI from Hugging Face...")
        ds = load_dataset("ai4bharat/MSMARCO-XI", split="train", streaming=True)

        documents = []
        for i, row in enumerate(ds):
            if i >= max_rows:
                break
            text = _find_text_field(row)
            if not text:
                continue
            doc_id = _find_id_field(row, i)
            metadata = {k: v for k, v in row.items() if isinstance(v, (str, int, float, bool))}
            documents.append(DocumentRecord(document_id=doc_id, text=text, metadata=metadata))

        logger.info(f"Loaded {len(documents)} documents from ai4bharat/MSMARCO-XI.")
        return documents
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Could not load dataset from Hugging Face ({exc}). Falling back to local sample.")
        return load_local_sample()


def load_local_sample() -> List[DocumentRecord]:
    import json

    if not SAMPLE_CORPUS_PATH.exists():
        raise FileNotFoundError(
            f"No local sample corpus found at {SAMPLE_CORPUS_PATH}. "
            f"Run this on a machine with internet access, or add a sample_corpus.jsonl."
        )
    documents = []
    with open(SAMPLE_CORPUS_PATH, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            text = _find_text_field(row)
            doc_id = _find_id_field(row, i)
            documents.append(DocumentRecord(document_id=doc_id, text=text, metadata=row.get("metadata", {})))
    return documents