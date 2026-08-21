"""
Offline preprocessing script to load dataset, chunk documents, and persist processed output locally.
Usage:
    python scripts/build_chunks.py --strategy fixed_overlap --limit 500
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add project root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.logging import logger
from app.schemas import DocumentRecord, ChunkRecord
from app.retrieval.ingestion import load_msmarco_dataset
from app.retrieval.chunking import get_chunker


def parse_args():
    parser = argparse.ArgumentParser(description="Build offline chunks from MSMARCO-XI dataset.")
    parser.add_argument(
        "--strategy",
        type=str,
        default="fixed_overlap",
        choices=["fixed_overlap", "fixed", "sentence", "passage_metadata", "metadata"],
        help="Chunking strategy to apply.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Number of query rows to ingest from dataset (default: 200).",
    )
    parser.add_argument(
        "--language",
        type=str,
        default="hin",
        help="Language split to load (hin, ben, tam, tel, etc.).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory to save chunks.jsonl and stats.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("==================================================")
    print("        Offline Chunk Preprocessing               ")
    print("==================================================")
    print(f"Dataset:       ai4bharat/MSMARCO-XI ({args.language})")
    print(f"Strategy:      {args.strategy}")
    print(f"Limit (rows):  {args.limit}")
    print(f"Output Dir:    {args.output_dir}")
    print("--------------------------------------------------\n")

    # 1. Load and normalize dataset
    docs: list[DocumentRecord] = load_msmarco_dataset(
        language=args.language,
        split="validation",
        limit=args.limit,
    )

    if not docs:
        print("ERROR: No documents loaded.")
        sys.exit(1)

    # 2. Chunk documents using selected strategy
    chunker = get_chunker(args.strategy)
    chunks: list[ChunkRecord] = chunker.chunk_batch(docs)

    # 3. Compute statistics
    chunk_lengths = [len(c.text) for c in chunks] if chunks else [0]
    avg_size = sum(chunk_lengths) / len(chunk_lengths) if chunk_lengths else 0
    min_size = min(chunk_lengths) if chunk_lengths else 0
    max_size = max(chunk_lengths) if chunk_lengths else 0

    stats = {
        "dataset": "ai4bharat/MSMARCO-XI",
        "language": args.language,
        "strategy": args.strategy,
        "documents_processed": len(docs),
        "chunks_generated": len(chunks),
        "avg_chunk_size_chars": round(avg_size, 2),
        "min_chunk_size_chars": min_size,
        "max_chunk_size_chars": max_size,
    }

    # 4. Save to disk
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    chunks_file = out_dir / "chunks.jsonl"
    stats_file = out_dir / "chunk_stats.json"

    with open(chunks_file, "w", encoding="utf-8") as f:
        for chk in chunks:
            f.write(chk.model_dump_json() + "\n")

    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    print("\n--- Processing Summary ---")
    print(f"Dataset:              {stats['dataset']}")
    print(f"Documents processed:  {stats['documents_processed']}")
    print(f"Strategy:             {stats['strategy']}")
    print(f"Chunks generated:     {stats['chunks_generated']}")
    print(f"Average chunk size:   {stats['avg_chunk_size_chars']} chars")
    print(f"Min chunk size:       {stats['min_chunk_size_chars']} chars")
    print(f"Max chunk size:       {stats['max_chunk_size_chars']} chars")
    print(f"\nPersisted chunks to: {chunks_file.resolve()}")
    print(f"Persisted stats to:  {stats_file.resolve()}")
    print("--------------------------------------------------")


if __name__ == "__main__":
    main()
