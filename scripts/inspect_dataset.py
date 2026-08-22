"""
Phase 3A — Dataset inspection.
Loads ai4bharat/MSMARCO-XI (or local sample fallback) and prints stats.
"""

import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.retrieval.dataset import load_msmarco_xi


def inspect(documents):
    print(f"\n=== Dataset Inspection ===")
    print(f"Total documents loaded: {len(documents)}")
    if not documents:
        print("No documents to inspect.")
        return

    lengths = [len(d.text) for d in documents]
    print(f"Char length — min: {min(lengths)}, max: {max(lengths)}, "
          f"mean: {statistics.mean(lengths):.1f}, median: {statistics.median(lengths):.1f}")

    print(f"\nSample metadata keys: {list(documents[0].metadata.keys())}")

    print("\n--- 3 sample documents ---")
    for i, d in enumerate(documents[:3]):
        preview = d.text[:200].replace("\n", " ")
        print(f"[{i}] id={d.document_id} ({len(d.text)} chars): {preview}{'...' if len(d.text) > 200 else ''}")


if __name__ == "__main__":
    documents = load_msmarco_xi(max_rows=2000)
    inspect(documents)