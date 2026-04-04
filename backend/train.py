from __future__ import annotations

from pathlib import Path
import site
import sys

user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.append(user_site)

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "prompts.csv"
MODEL_PATH = BASE_DIR / "models" / "classifier.pkl"


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    if df.empty:
        raise ValueError("Training dataset is empty.")

    x_train, x_test, y_train, y_test = train_test_split(
        df["prompt"],
        df["label"],
        test_size=0.2,
        random_state=42,
        stratify=df["label"],
    )

    pipeline = Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            (
                "clf",
                CalibratedClassifierCV(
                    estimator=LogisticRegression(max_iter=2000, class_weight="balanced"),
                    method="sigmoid",
                    cv=3,
                ),
            ),
        ]
    )

    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)

    print("Classification report:")
    print(classification_report(y_test, predictions))
    print("Confusion matrix:")
    print(confusion_matrix(y_test, predictions, labels=["weak", "moderate", "strong"]))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"Saved trained model to: {MODEL_PATH}")


if __name__ == "__main__":
    main()
