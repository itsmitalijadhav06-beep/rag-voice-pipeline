"""
Phase 3B — Build and persist chunks (all 3 strategies) from the dataset.
Chunks are saved to disk so they don't need recomputing every run.
"""

import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.logging import logger
from app.retrieval.chunker import chunk_document
from app.retrieval.dataset import load_msmarco_xi

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"
STRATEGIES = ["fixed", "semantic", "metadata_aware"]


def build_all_chunks(max_docs: int = 2000):
    documents = load_msmarco_xi(max_rows=max_docs)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for strategy in STRATEGIES:
        all_chunks = []
        for doc in documents:
            all_chunks.extend(chunk_document(doc.document_id, doc.text, strategy=strategy))

        out_path = OUTPUT_DIR / f"chunks_{strategy}.jsonl"
        with open(out_path, "w", encoding="utf-8") as f:
            for chunk in all_chunks:
                f.write(json.dumps(asdict(chunk)) + "\n")

        logger.info(f"[{strategy}] {len(all_chunks)} chunks saved to {out_path}")
        print(f"{strategy}: {len(all_chunks)} chunks -> {out_path}")


if __name__ == "__main__":
    build_all_chunks()