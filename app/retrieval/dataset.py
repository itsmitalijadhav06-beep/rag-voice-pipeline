"""
Dataset loading and normalization (Phase 3A).

Loads ai4bharat/MSMARCO-XI (or parquet streams) and converts rows into
normalized DocumentRecord structures, so chunking/embedding layers receive
clean, typed data.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logging import logger

SAMPLE_CORPUS_PATH = Path(__file__).resolve().parents[2] / "data" / "raw" / "sample_corpus.jsonl"

# Language code map for MSMARCO-XI files
LANG_MAP = {
    "as": "asm", "bn": "ben", "gu": "guj", "hi": "hin", "kn": "kan",
    "ml": "mal", "mr": "mar", "ne": "nep", "or": "ori", "pa": "pan",
    "sa": "san", "ta": "tam", "te": "tel", "ur": "urd"
}


@dataclass
class DocumentRecord:
    document_id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


def normalize_raw_row(row: dict, fallback_idx: int, language: str = "mr") -> List[DocumentRecord]:
    """Normalizes a raw dataset row into one or more DocumentRecords.
    MSMARCO-XI rows contain nested passage lists alongside queries and answers.
    """
    records: List[DocumentRecord] = []
    query_id = row.get("query_id")
    if query_id is None or (hasattr(query_id, "__len__") and len(query_id) == 0):
        query_id = fallback_idx

    if language.lower() == "en":
        query = row.get("Eng_Query") or row.get("query") or ""
        answer = row.get("Eng_Answer") or row.get("Answer") or ""
    else:
        query = row.get("query") or row.get("Eng_Query") or ""
        answer = row.get("Answer") or row.get("Eng_Answer") or ""

    if not isinstance(query, str):
        query = str(query)

    if not isinstance(answer, str):
        answer = str(answer)

    query_type = str(row.get("query_type") or "description")

    base_metadata = {
        "query_id": str(query_id),
        "query": query,
        "answer": answer,
        "query_type": query_type,
        "language": language,
    }
    if row.get("Eng_Query"):
        base_metadata["eng_query"] = str(row["Eng_Query"])
    if row.get("Eng_Answer"):
        base_metadata["eng_answer"] = str(row["Eng_Answer"])

    passages_obj = row.get("passages")

    # Case 1: Passages is a dict containing Translated_passages / English_passages
    if isinstance(passages_obj, dict):
        translated = None
        if language.lower() == "en":
            translated = passages_obj.get("English_passages")
        else:
            translated = passages_obj.get("Translated_passages")
            if translated is None:
                translated = passages_obj.get("English_passages")
        translated_list = list(translated) if translated is not None else []

        selected = passages_obj.get("is_selected")
        selected_list = list(selected) if selected is not None else []

        for p_idx, text in enumerate(translated_list):
            if not isinstance(text, str) or not text.strip():
                continue
            is_sel = int(selected_list[p_idx]) if p_idx < len(selected_list) else 0
            doc_id = f"msmarco_{query_id}_{p_idx}"
            meta = {**base_metadata, "passage_index": p_idx, "is_selected": is_sel}
            records.append(DocumentRecord(document_id=doc_id, text=text.strip(), metadata=meta))

    # Case 2: Passages is a list/array of passage strings or dicts
    elif hasattr(passages_obj, "__iter__") and not isinstance(passages_obj, (str, bytes)):
        p_list = list(passages_obj)
        for p_idx, item in enumerate(p_list):
            if isinstance(item, str) and item.strip():
                doc_id = f"msmarco_{query_id}_{p_idx}"
                meta = {**base_metadata, "passage_index": p_idx}
                records.append(DocumentRecord(document_id=doc_id, text=item.strip(), metadata=meta))
            elif isinstance(item, dict):
                text = item.get("passage_text") or item.get("text") or ""
                if isinstance(text, str) and text.strip():
                    doc_id = str(item.get("passage_id", f"msmarco_{query_id}_{p_idx}"))
                    meta = {**base_metadata, "passage_index": p_idx, "is_selected": item.get("is_selected", 0)}
                    records.append(DocumentRecord(document_id=doc_id, text=text.strip(), metadata=meta))

    # Case 3: Flat text field fallback (e.g., passage / text / context)
    else:
        text = ""
        for key in ("passage", "text", "context", "document"):
            val = row.get(key)
            if isinstance(val, str) and val.strip():
                text = val.strip()
                break
        if not text and answer.strip():
            text = answer.strip()

        if text:
            doc_id = f"msmarco_{query_id}_0"
            meta = {**base_metadata, "passage_index": 0}
            records.append(DocumentRecord(document_id=doc_id, text=text, metadata=meta))

    return records



def load_msmarco_xi(
    language: str = "mr",
    split: str = "train",
    limit: int = 1000,
    max_rows: Optional[int] = None,
) -> List[DocumentRecord]:
    """Loads and normalizes real ai4bharat/MSMARCO-XI records with support for
    language selection, split selection, and controlled subset limit.
    """
    effective_limit = limit if limit is not None else (max_rows or 1000)
    
    # If English, load Hindi parquet as the container of original English passages
    target_lang = "hi" if language.lower() == "en" else language
    lang_code = LANG_MAP.get(target_lang.lower(), target_lang.lower())
    split_name = "train" if "train" in split.lower() else "validation"
    file_prefix = "train" if split_name == "train" else "val"
    parquet_filename = f"{split_name}/{lang_code}{file_prefix}.parquet"

    logger.info(f"Loading ai4bharat/MSMARCO-XI dataset file '{parquet_filename}' (limit={effective_limit})...")

    # Strategy 1: Direct file download using hf_hub_download & pyarrow
    try:
        from huggingface_hub import hf_hub_download
        import pyarrow.parquet as pq

        try:
            local_path = hf_hub_download(
                repo_id="ai4bharat/MSMARCO-XI",
                filename=parquet_filename,
                repo_type="dataset",
                local_files_only=True,
            )
        except Exception:
            local_path = hf_hub_download(
                repo_id="ai4bharat/MSMARCO-XI",
                filename=parquet_filename,
                repo_type="dataset",
                local_files_only=False,
            )

        pf = pq.ParquetFile(local_path)
        documents: List[DocumentRecord] = []
        for rg_idx in range(pf.num_row_groups):
            df_rg = pf.read_row_group(rg_idx).to_pandas()
            for i, row in df_rg.iterrows():
                recs = normalize_raw_row(row.to_dict(), i, language=language)
                documents.extend(recs)
                if len(documents) >= effective_limit:
                    documents = documents[:effective_limit]
                    break
            if len(documents) >= effective_limit:
                break




        if documents:
            logger.info(f"Successfully loaded {len(documents)} normalized records via hf_hub_download Parquet file.")
            return documents
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Direct hf_hub_download failed ({exc}). Trying streaming load_dataset...")

    # Strategy 2: Stream via Hugging Face datasets load_dataset
    try:
        from datasets import load_dataset

        ds = load_dataset(
            "ai4bharat/MSMARCO-XI",
            data_files={split_name: parquet_filename},
            split=split_name,
            streaming=True,
        )
        documents = []
        for i, row in enumerate(ds):
            recs = normalize_raw_row(row, i, language=language)
            documents.extend(recs)
            if len(documents) >= effective_limit:
                documents = documents[:effective_limit]
                break

        if documents:
            logger.info(f"Loaded {len(documents)} normalized records via streaming Hugging Face datasets.")
            return documents
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Streaming load_dataset failed ({exc}). Falling back to local sample...")

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
            recs = normalize_raw_row(row, i, language="en")
            documents.extend(recs)
    logger.info(f"Loaded {len(documents)} fallback documents from local sample corpus.")
    return documents