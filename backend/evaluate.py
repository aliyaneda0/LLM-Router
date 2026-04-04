from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "prompts.csv"
MODEL_PATH = BASE_DIR / "models" / "classifier.pkl"
EVAL_PATH = BASE_DIR / "models" / "evaluation.json"


def main() -> None:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}. Train first.")

    df = pd.read_csv(DATA_PATH)
    _, x_test, _, y_test = train_test_split(
        df["prompt"],
        df["label"],
        test_size=0.2,
        random_state=42,
        stratify=df["label"],
    )

    model = joblib.load(MODEL_PATH)
    predictions = model.predict(x_test)

    labels = ["weak", "moderate", "strong"]
    report = classification_report(y_test, predictions, output_dict=True)
    matrix = confusion_matrix(y_test, predictions, labels=labels)
    metrics = {
        "accuracy": round(accuracy_score(y_test, predictions), 4),
        "labels": labels,
        "confusion_matrix": matrix.tolist(),
        "classification_report": report,
    }

    EVAL_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"Accuracy: {metrics['accuracy']}")
    print("Confusion matrix:")
    print(matrix)
    print(f"Saved evaluation report to: {EVAL_PATH}")


if __name__ == "__main__":
    main()
