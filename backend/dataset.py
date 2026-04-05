from __future__ import annotations

from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_prompt_datasets() -> pd.DataFrame:
    csv_paths = sorted(DATA_DIR.glob("prompts*.csv"))
    if not csv_paths:
        raise FileNotFoundError("No prompt CSV files found in the data directory.")

    frames = [pd.read_csv(path) for path in csv_paths]
    combined = pd.concat(frames, ignore_index=True)
    combined = combined.dropna(subset=["prompt", "label"])
    combined["prompt"] = combined["prompt"].astype(str).str.strip()
    combined["label"] = combined["label"].astype(str).str.strip()
    combined = combined[combined["prompt"] != ""]
    combined = combined.drop_duplicates(subset=["prompt", "label"]).reset_index(drop=True)
    return combined
