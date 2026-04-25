import argparse
import csv
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from document_verifier.ml_features import extract_advanced_features


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", type=Path)
    parser.add_argument("--output", type=Path, default=Path("models/document_model.joblib"))
    args = parser.parse_args()

    samples = _load_directory_dataset(args.dataset_dir)

    X, y = [], []

    for image_path, label in samples:
        try:
            features = extract_advanced_features(image_path)
            X.append(features)
            y.append(label)
        except Exception as e:
            print(f"Skipping {image_path}: {e}")

    X = np.array(X)
    y = np.array(y)

    x_train, x_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y
    )

    model = make_pipeline(
        StandardScaler(),
        RandomForestClassifier(
            n_estimators=300,
            class_weight="balanced"
        )
    )

    model.fit(x_train, y_train)

    preds = model.predict(x_test)
    probs = model.predict_proba(x_test)[:, 1]

    print(classification_report(y_test, preds))
    print("ROC-AUC:", roc_auc_score(y_test, probs))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.output)

    print("✅ Model saved:", args.output)


def _load_directory_dataset(dataset_dir: Path):
    samples = []
    for folder_name, label in (("authentic", 0), ("tampered", 1)):
        folder = dataset_dir / folder_name
        if not folder.exists():
            continue

        for path in folder.rglob("*"):
            if path.suffix.lower() in IMAGE_EXTENSIONS:
                samples.append((path, label))

    return samples


if __name__ == "__main__":
    main()