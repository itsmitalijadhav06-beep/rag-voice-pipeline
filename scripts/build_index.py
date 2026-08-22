"""
Phase 3C — Build and persist FAISS indices for all chunking strategies.
This is the OFFLINE indexing step — runtime retrieve() searches pre-built indexes
under data/index/<strategy>/ and NEVER rebuilds at query time.

Usage:
    python scripts/build_index.py --language mr --split validation --limit 500 --strategies fixed sentence semantic
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.retrieval.dataset import load_msmarco_xi
from app.retrieval.pipeline import RetrievalPipeline


def build_all_indices(
    language: str = "mr",
    split: str = "validation",
    limit: int = 500,
    strategies: list = None,
):
    strategies = strategies or ["fixed", "sentence", "semantic"]
    print(f"Loading {limit} documents from MSMARCO-XI ({language}, {split})...")
    start = time.perf_counter()
    documents = load_msmarco_xi(language=language, split=split, limit=limit)
    print(f"Loaded {len(documents)} document records in {time.perf_counter() - start:.2f}s.")

    pipeline = RetrievalPipeline()
    print(f"Building FAISS indices for strategies: {strategies}...")
    pipeline.build_index(
        documents,
        strategies=strategies,
        language=language,
        split=split,
        limit=limit
    )

    print(f"\nSuccessfully built and saved indices:")
    for strat, store in pipeline.stores.items():
        print(f"  - [{strat}]: {len(store._chunks)} chunks, vector dim={store.dimension}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build offline FAISS vector indices from MSMARCO-XI.")
    parser.add_argument("--language", type=str, default="mr", help="Language code (e.g. mr, hi, en)")
    parser.add_argument("--split", type=str, default="validation", help="Split name (train, validation)")
    parser.add_argument("--limit", type=int, default=500, help="Maximum documents to index")
    parser.add_argument(
        "--strategies",
        nargs="+",
        default=["fixed", "sentence", "semantic"],
        help="Strategies to index (fixed, sentence, semantic)",
    )
    args = parser.parse_args()

    build_all_indices(
        language=args.language,
        split=args.split,
        limit=args.limit,
        strategies=args.strategies,
    )