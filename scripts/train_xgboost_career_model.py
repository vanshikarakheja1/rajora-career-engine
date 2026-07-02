import json
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from xgboost import XGBClassifier


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from career_engine.ml.features import MODEL_FEATURES  # noqa: E402


DATASET_PATH = PROJECT_ROOT / "data" / "raw" / "students_5000.xlsx"
MODEL_PATH = PROJECT_ROOT / "models" / "xgboost_career_classifier.joblib"
METRICS_PATH = PROJECT_ROOT / "reports" / "xgboost_career_metrics.json"
TARGET_COLUMN = "recommended_career_1"
RANDOM_STATE = 42


def load_training_data() -> tuple[pd.DataFrame, pd.Series]:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    df = pd.read_excel(DATASET_PATH).dropna(subset=[TARGET_COLUMN])
    available_features = [feature for feature in MODEL_FEATURES if feature in df.columns]

    if not available_features:
        raise ValueError("No matching model features were found in the dataset.")

    return df[available_features], df[TARGET_COLUMN]


def build_model(X: pd.DataFrame) -> Pipeline:
    numeric_features = X.select_dtypes(include=["number", "bool"]).columns.tolist()
    categorical_features = X.select_dtypes(exclude=["number", "bool"]).columns.tolist()

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median"))]), numeric_features),
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_features,
            ),
        ]
    )

    classifier = XGBClassifier(
        n_estimators=250,
        max_depth=4,
        learning_rate=0.06,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="multi:softprob",
        eval_metric="mlogloss",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )


def main() -> None:
    X, y = load_training_data()

    label_encoder = LabelEncoder()
    encoded_y = label_encoder.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        encoded_y,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=encoded_y,
    )

    model = build_model(X)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    report = classification_report(
        y_test,
        predictions,
        target_names=label_encoder.classes_,
        output_dict=True,
        zero_division=0,
    )

    artifact = {
        "model": model,
        "label_encoder": label_encoder,
        "features": X.columns.tolist(),
        "target_column": TARGET_COLUMN,
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, MODEL_PATH)

    metrics = {
        "model": "XGBoost Career Classifier",
        "dataset": DATASET_PATH.name,
        "target_column": TARGET_COLUMN,
        "rows_used": int(len(X)),
        "features_used": int(X.shape[1]),
        "training_rows": int(len(X_train)),
        "testing_rows": int(len(X_test)),
        "accuracy": round(float(accuracy), 4),
        "classes": label_encoder.classes_.tolist(),
        "classification_report": report,
    }
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print("Model: XGBoost Career Classifier")
    print(f"Dataset: {DATASET_PATH.name}")
    print(f"Target column: {TARGET_COLUMN}")
    print(f"Rows used: {len(X)}")
    print(f"Features used: {X.shape[1]}")
    print(f"Training rows: {len(X_train)}")
    print(f"Testing rows: {len(X_test)}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Saved model: {MODEL_PATH}")
    print(f"Saved metrics: {METRICS_PATH}")


if __name__ == "__main__":
    main()
