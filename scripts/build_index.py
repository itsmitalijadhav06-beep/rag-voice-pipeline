"""
Phase 3C — Build and persist FAISS indices for all chunking strategies.
This is the OFFLINE indexing step — runtime /query only embeds the query
and searches, never rebuilds the index.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.retrieval.dataset import load_msmarco_xi
from app.retrieval.pipeline import RetrievalPipeline


def build_all_indices(max_docs: int = 2000):
    documents = load_msmarco_xi(max_rows=max_docs)
    pipeline = RetrievalPipeline()
    pipeline.build_index(documents)
    print(f"Built and saved indices for strategies: {list(pipeline.stores.keys())}")


if __name__ == "__main__":
    build_all_indices()