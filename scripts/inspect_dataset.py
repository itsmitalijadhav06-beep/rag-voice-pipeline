"""
Phase 3A — Dataset inspection script.
Loads ai4bharat/MSMARCO-XI with configurable language, split, and row limit.
Usage:
    python scripts/inspect_dataset.py --language mr --split validation --limit 100
"""

import argparse
import statistics
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


from app.retrieval.dataset import load_msmarco_xi


def inspect(documents, language: str, split: str):
    print(f"\n=== Dataset Inspection (ai4bharat/MSMARCO-XI) ===")
    print(f"Language: {language} | Split: {split}")
    print(f"Total normalized documents loaded: {len(documents)}")
    if not documents:
        print("No documents to inspect.")
        return

    lengths = [len(d.text) for d in documents]
    print(f"Char length — min: {min(lengths)}, max: {max(lengths)}, "
          f"mean: {statistics.mean(lengths):.1f}, median: {statistics.median(lengths):.1f}")

    sample_meta = documents[0].metadata
    print(f"\nSample metadata keys: {list(sample_meta.keys())}")
    print(f"Sample query_id: {sample_meta.get('query_id')}")
    print(f"Sample query: {sample_meta.get('query')}")
    print(f"Sample answer: {sample_meta.get('answer')}")

    print("\n--- 3 sample normalized document records ---")
    for i, d in enumerate(documents[:3]):
        preview = d.text[:200].replace("\n", " ")
        print(f"[{i}] id={d.document_id} ({len(d.text)} chars): {preview}{'...' if len(d.text) > 200 else ''}")
        print(f"    metadata: {d.metadata}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect ai4bharat/MSMARCO-XI dataset.")
    parser.add_argument("--language", type=str, default="mr", help="Language code (e.g. mr, hi, en)")
    parser.add_argument("--split", type=str, default="validation", help="Split name (train, validation)")
    parser.add_argument("--limit", type=int, default=100, help="Maximum normalized documents to inspect")
    args = parser.parse_args()

    documents = load_msmarco_xi(language=args.language, split=args.split, limit=args.limit)
    inspect(documents, language=args.language, split=args.split)