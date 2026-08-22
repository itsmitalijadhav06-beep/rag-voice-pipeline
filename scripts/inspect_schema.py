"""
Phase 3A — Raw schema inspection script.
Shows raw MSMARCO-XI parquet structure and column schema.
Usage:
    python scripts/inspect_schema.py --language mr --split validation --limit 5
"""

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.retrieval.dataset import LANG_MAP, load_msmarco_xi


def inspect_schema(language: str = "mr", split: str = "validation", limit: int = 5):
    print(f"\n=== MSMARCO-XI Parquet Raw Schema Inspection ===")
    print(f"Target Language: {language} | Split: {split}")

    lang_code = LANG_MAP.get(language.lower(), language.lower())
    split_name = "train" if "train" in split.lower() else "validation"
    file_prefix = "train" if split_name == "train" else "val"
    parquet_filename = f"{split_name}/{lang_code}{file_prefix}.parquet"

    print(f"Target Parquet file: {parquet_filename}")

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
        arrow_schema = pf.schema.to_arrow_schema()
        print(f"\nParquet Schema Columns ({len(arrow_schema.names)} fields):")
        for field in arrow_schema:
            print(f"  - {field.name}: {field.type}")


        first_rg = pf.read_row_group(0).to_pandas().head(limit)
        print(f"\nSample Row 0 Raw Data:")
        row_0 = first_rg.iloc[0].to_dict()
        for k, v in row_0.items():
            preview = str(v)[:120].replace("\n", " ")
            print(f"  {k} ({type(v).__name__}): {preview}")

    except Exception as exc:  # noqa: BLE001
        print(f"Failed to inspect raw Parquet schema directly ({exc}). Using normalized inspection...")
        documents = load_msmarco_xi(language=language, split=split, limit=limit)
        if documents:
            print(f"Normalized documents sample metadata: {documents[0].metadata}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect raw MSMARCO-XI schema.")
    parser.add_argument("--language", type=str, default="mr", help="Language code (e.g. mr, hi, en)")
    parser.add_argument("--split", type=str, default="validation", help="Split name (train, validation)")
    parser.add_argument("--limit", type=int, default=5, help="Number of rows to inspect")
    args = parser.parse_args()

    inspect_schema(language=args.language, split=args.split, limit=args.limit)