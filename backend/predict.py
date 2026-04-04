from __future__ import annotations

from pathlib import Path
from typing import Any
import site
import sys

user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.append(user_site)

import joblib


BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "classifier.pkl"


def load_model() -> Any:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found at {MODEL_PATH}. Run backend/train.py first."
        )
    return joblib.load(MODEL_PATH)


def predict_prompt(prompt: str) -> dict[str, Any]:
    model = load_model()
    predicted_class = model.predict([prompt])[0]
    probabilities = model.predict_proba([prompt])[0]
    labels = list(model.classes_)
    scores = {label: float(score) for label, score in zip(labels, probabilities)}
    confidence = max(scores.values())
    return {
        "predicted_class": str(predicted_class),
        "confidence": confidence,
        "class_probabilities": scores,
    }
