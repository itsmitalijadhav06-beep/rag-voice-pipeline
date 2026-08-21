"""
Inspect exact schema of MSMARCO-XI dataset passages and document fields.
"""
import sys
import pandas as pd
from huggingface_hub import hf_hub_download

sys.stdout.reconfigure(encoding='utf-8')

def inspect():
    path = hf_hub_download(repo_id='ai4bharat/MSMARCO-XI', filename='validation/hinval.parquet', repo_type='dataset')
    df = pd.read_parquet(path)
    
    print(f"Total rows in sample split: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")
    
    sample = df.iloc[0]
    print("\n--- SAMPLE RECORD ---")
    for col in df.columns:
        val = sample[col]
        print(f"\n[Column: {col}] (Type: {type(val).__name__})")
        if col == "passages":
            print("Passages keys:", list(val.keys()) if isinstance(val, dict) else type(val))
            if isinstance(val, dict):
                for pk, pv in val.items():
                    print(f"  passages['{pk}'] type: {type(pv).__name__}, len: {len(pv) if hasattr(pv, '__len__') else 'N/A'}")
                    if hasattr(pv, '__len__') and len(pv) > 0:
                        print(f"    Item 0 preview: {str(pv[0])[:200]}")
        else:
            print(f"Preview: {str(val)[:200]}")

if __name__ == "__main__":
    inspect()
