"""
Phase 3A — Raw schema inspection.
Shows the RAW Hugging Face dataset structure (before normalization into
DocumentRecord) — splits, column names, and a raw sample row.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def inspect_schema():
    from datasets import get_dataset_config_names, get_dataset_split_names, load_dataset

    dataset_name = "ai4bharat/MSMARCO-XI"

    try:
        configs = get_dataset_config_names(dataset_name)
        print(f"Available configs: {configs}")
    except Exception as exc:
        print(f"Could not list configs: {exc}")
        configs = [None]

    for config in configs:
        try:
            splits = get_dataset_split_names(dataset_name, config)
            print(f"Config '{config}' splits: {splits}")
        except Exception as exc:
            print(f"Could not list splits for config '{config}': {exc}")

    print("\nLoading first split, first row for raw schema...")
    ds = load_dataset(dataset_name, split="train[:1]")
    row = ds[0]
    print(f"\nRaw columns: {list(row.keys())}")
    for k, v in row.items():
        preview = str(v)[:150]
        print(f"  {k}: ({type(v).__name__}) {preview}")


if __name__ == "__main__":
    inspect_schema()