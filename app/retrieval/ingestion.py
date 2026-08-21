"""
Dataset ingestion & normalization layer for MSMARCO-XI.
"""

from typing import List, Generator, Optional, Dict, Any
from pathlib import Path
import pandas as pd
from datasets import load_dataset
from huggingface_hub import hf_hub_download

from app.core.logging import logger
from app.schemas import DocumentRecord


def normalize_msmarco_row(row: Dict[str, Any], row_idx: int = 0) -> List[DocumentRecord]:
    """
    Normalizes a raw MSMARCO-XI dataset record into standardized DocumentRecord objects.
    Each candidate passage in the row becomes a distinct DocumentRecord with rich metadata.
    """
    query_id = row.get("query_id", row_idx)
    query_type = row.get("query_type", "UNKNOWN")
    source_lang = row.get("source_lang", "eng_Latn")
    target_lang = row.get("target_lang", "hin_Deva")
    eng_query = row.get("Eng_Query", "")
    query = row.get("query", "")
    eng_answer = row.get("Eng_Answer", "")
    answer = row.get("Answer", "")

    passages_dict = row.get("passages") or {}
    translated_passages = passages_dict.get("Translated_passages", [])
    english_passages = passages_dict.get("English_passages", [])
    is_selected_list = passages_dict.get("is_selected", [])

    # Prefer translated passages if available, fallback to english passages
    passage_texts = translated_passages if len(translated_passages) > 0 else english_passages

    documents: List[DocumentRecord] = []

    if isinstance(passage_texts, (list, tuple, range)) or hasattr(passage_texts, "__len__"):
        for p_idx, text_item in enumerate(passage_texts):
            text_str = str(text_item).strip() if text_item is not None else ""
            if not text_str:
                continue

            sel_val = 0
            if isinstance(is_selected_list, (list, tuple, range)) or hasattr(is_selected_list, "__len__"):
                if p_idx < len(is_selected_list):
                    sel_val = int(is_selected_list[p_idx])

            doc_id = f"doc_{query_id}_p{p_idx}"
            metadata = {
                "query_id": query_id,
                "passage_index": p_idx,
                "is_selected": sel_val,
                "query_type": query_type,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "eng_query": eng_query,
                "query": query,
                "eng_answer": eng_answer,
                "answer": answer,
                "language": target_lang.split("_")[0] if "_" in target_lang else target_lang,
            }

            documents.append(
                DocumentRecord(
                    document_id=doc_id,
                    text=text_str,
                    metadata=metadata,
                )
            )

    # Fallback if passages dictionary was empty or missing
    if not documents:
        raw_text = str(row.get("text", "") or eng_query or query).strip()
        if raw_text:
            documents.append(
                DocumentRecord(
                    document_id=f"doc_{query_id}_fallback",
                    text=raw_text,
                    metadata={
                        "query_id": query_id,
                        "query_type": query_type,
                        "source_lang": source_lang,
                        "target_lang": target_lang,
                    },
                )
            )

    return documents


def load_msmarco_dataset(
    language: str = "hin",
    split: str = "validation",
    limit: Optional[int] = None,
    dataset_name: str = "ai4bharat/MSMARCO-XI",
) -> List[DocumentRecord]:
    """
    Downloads/loads MSMARCO-XI parquet split and converts rows into DocumentRecord objects.
    """
    filename = f"{split}/{language}val.parquet" if "val" in split else f"{split}/{language}train.parquet"
    logger.info("Loading dataset %s (filename: %s)...", dataset_name, filename)

    try:
        parquet_path = hf_hub_download(repo_id=dataset_name, filename=filename, repo_type="dataset")
        df = pd.read_parquet(parquet_path)
    except Exception as e:
        logger.warning("Failed to load parquet file '%s' directly: %s. Attempting fallback...", filename, e)
        # Attempt fallback via Hugging Face load_dataset
        ds = load_dataset(dataset_name, split=split, streaming=True)
        df_rows = []
        for i, item in enumerate(ds):
            df_rows.append(item)
            if limit and len(df_rows) >= limit:
                break
        df = pd.DataFrame(df_rows)

    if limit and len(df) > limit:
        df = df.iloc[:limit]

    all_docs: List[DocumentRecord] = []
    for idx, row in df.iterrows():
        docs = normalize_msmarco_row(row.to_dict(), row_idx=idx)
        all_docs.extend(docs)

    logger.info("Ingested %d documents from %d dataset query rows.", len(all_docs), len(df))
    return all_docs
