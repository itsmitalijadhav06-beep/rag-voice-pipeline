"""
Direct inspection script for ai4bharat/MSMARCO-XI dataset.
"""
import sys
from datasets import load_dataset

def inspect():
    dataset_name = "ai4bharat/MSMARCO-XI"
    # MSMARCO-XI configs are typically language codes or 'english', 'hindi', etc.
    # Let's try default / english first
    for config_candidate in [None, "english", "en", "hindi", "hi"]:
        print(f"\n--- Trying config: {config_candidate} ---")
        try:
            if config_candidate:
                ds = load_dataset(dataset_name, config_candidate, split="train", streaming=True)
            else:
                ds = load_dataset(dataset_name, split="train", streaming=True)
            
            sample = next(iter(ds))
            print("SUCCESS!")
            print("Config used:", config_candidate)
            print("Fields:", list(sample.keys()))
            for k, v in sample.items():
                print(f"  {k} ({type(v).__name__}): {str(v)[:200]}")
            break
        except Exception as e:
            print(f"Config '{config_candidate}' failed: {e}")

if __name__ == "__main__":
    inspect()
