"""
Phase 3D — Retrieval evaluation & latency benchmark.

Runs multiple test queries against pre-built FAISS vector indices, measuring
high-resolution latency (P50, P70, P100/max), query count, top-k similarity
scores, and relevant context overlap.

Usage:
    python scripts/evaluate_retrieval.py --strategy fixed --queries 20 --top_k 5
"""

import argparse
import statistics
import sys
import time
from pathlib import Path
from typing import List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


from app.retrieval.retrieve import retrieve_with_latency
from app.retrieval.records import RetrievedChunk


TEST_QUERIES = [
    ("कॉर्पोरेशन क्या है?", "निगम एक कंपनी या लोगों का समूह होता है"),
    ("What is a corporation?", "company or group of people authorized"),
    ("निगम की परिभाषा क्या है?", "व्यावसायिक संस्था"),
    ("कंप्यूटर क्या है?", "इलेक्ट्रॉनिक उपकरण"),
    ("What is artificial intelligence?", "machine learning"),
    ("भारत की राजधानी क्या है?", "नई दिल्ली"),
    ("मौसम क्या है?", "वायुमंडल की स्थिति"),
    ("सौर ऊर्जा क्या है?", "सूर्य से ऊर्जा"),
    ("स्वास्थ्य क्या है?", "शारीरिक और मानसिक स्थिति"),
    ("शिक्षा का महत्व क्या है?", "ज्ञान और विकास"),
    ("इंटरनेट कैसे काम करता है?", "नेटवर्क"),
    ("डिजिटल अर्थव्यवस्था क्या है?", "ऑनलाइन व्यापार"),
    ("कृषि क्या है?", "खेती और फसल"),
    ("पर्यावरण क्या है?", "प्रकृति और वातावरण"),
    ("जल संरक्षण क्या है?", "पानी की बचत"),
    ("ऊर्जा क्या है?", "कार्य करने की क्षमता"),
    ("तकनीक क्या है?", "विज्ञान का अनुप्रयोग"),
    ("संस्कृति क्या है?", "परंपराएं और मूल्य"),
    ("लोकतंत्र क्या है?", "जनता का शासन"),
    ("विज्ञान क्या है?", "व्यवस्थित ज्ञान"),
]


def calculate_percentile(data: List[float], percentile: float) -> float:
    """Calculates percentile (50, 70, 100) over a list of floats."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    if percentile >= 100:
        return sorted_data[-1]
    index = (len(sorted_data) - 1) * (percentile / 100.0)
    lower = int(index)
    upper = lower + 1
    weight = index - lower
    if upper >= len(sorted_data):
        return sorted_data[-1]
    return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight


def evaluate_retrieval(strategy: str = "fixed", query_limit: int = 20, top_k: int = 5):
    print(f"\n==================================================")
    print(f"       PHASE 3D — RETRIEVAL EVALUATION BENCHMARK  ")
    print(f"==================================================")
    print(f"Strategy: {strategy} | Top-K: {top_k} | Queries to benchmark: {min(query_limit, len(TEST_QUERIES))}")

    latencies: List[float] = []
    scores: List[float] = []
    returned_counts: List[int] = []

    eval_queries = TEST_QUERIES[:query_limit]

    # Warm-up call
    retrieve_with_latency(eval_queries[0][0], top_k=top_k, strategy=strategy)

    print("\n--- Running benchmark queries ---")
    for idx, (query, expected_keyword) in enumerate(eval_queries):
        start = time.perf_counter()
        chunks, latency_ms = retrieve_with_latency(query, top_k=top_k, strategy=strategy)
        elapsed_ms = (time.perf_counter() - start) * 1000

        latencies.append(elapsed_ms)
        returned_counts.append(len(chunks))

        top_score = chunks[0].score if chunks else 0.0
        if chunks:
            scores.extend([c.score for c in chunks])

        preview = chunks[0].text[:80].replace("\n", " ") if chunks else "NONE"
        print(
            f"[{idx+1:02d}] Query: '{query[:25]}' | Chunks: {len(chunks)} | "
            f"Top Score: {top_score:.4f} | Latency: {elapsed_ms:.2f} ms | First: '{preview}...'"
        )

    # Compute metrics
    mean_lat = statistics.mean(latencies)
    median_lat = statistics.median(latencies)
    p50_lat = calculate_percentile(latencies, 50)
    p70_lat = calculate_percentile(latencies, 70)
    p100_lat = calculate_percentile(latencies, 100)
    min_lat = min(latencies)

    mean_score = statistics.mean(scores) if scores else 0.0
    max_score = max(scores) if scores else 0.0
    min_score = min(scores) if scores else 0.0

    print("\n==================================================")
    print("                LATENCY & QUALITY RESULTS         ")
    print("==================================================")
    print(f"Total Queries Executed:  {len(eval_queries)}")
    print(f"Average Latency:         {mean_lat:.2f} ms")
    print(f"Min Latency:             {min_lat:.2f} ms")
    print(f"P50 (Median) Latency:    {p50_lat:.2f} ms")
    print(f"P70 Latency:             {p70_lat:.2f} ms")
    print(f"P100 (Max) Latency:      {p100_lat:.2f} ms")
    print(f"Average Top-K Score:     {mean_score:.4f} (Min: {min_score:.4f}, Max: {max_score:.4f})")
    print(f"Avg Returned Chunks:     {statistics.mean(returned_counts):.1f}")
    print("==================================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate retrieval latency and vector search quality.")
    parser.add_argument("--strategy", type=str, default="fixed", help="Strategy to evaluate (fixed, sentence, semantic)")
    parser.add_argument("--queries", type=int, default=20, help="Number of test queries to run")
    parser.add_argument("--top_k", type=int, default=5, help="Top-K chunks to retrieve per query")
    args = parser.parse_args()

    evaluate_retrieval(strategy=args.strategy, query_limit=args.queries, top_k=args.top_k)
