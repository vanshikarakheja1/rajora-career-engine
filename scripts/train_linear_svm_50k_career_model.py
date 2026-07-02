import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.svm import LinearSVC


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = PROJECT_ROOT / "data" / "raw" / "student_profiles_50k.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "linear_svm_50k_career_classifier.joblib"
METRICS_PATH = PROJECT_ROOT / "reports" / "linear_svm_50k_career_metrics.json"
TARGET_COLUMN = "career_goal"
RANDOM_STATE = 42

NUMERIC_FEATURES = [
    "cgpa",
    "class_10_percentage",
    "class_12_percentage",
    "projects_count",
    "internships_count",
    "hackathons",
    "expected_salary_lpa",
]

CATEGORICAL_FEATURES = [
    "education_level",
    "branch",
    "specialization",
    "preferred_work_mode",
]

TEXT_FEATURES = [
    "skills",
    "skill_levels",
    "interests",
    "certifications",
]


def load_training_data() -> tuple[pd.DataFrame, pd.Series]:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH).dropna(subset=[TARGET_COLUMN])
    features = NUMERIC_FEATURES + CATEGORICAL_FEATURES + TEXT_FEATURES
    X = df[features].copy()

    for column in TEXT_FEATURES:
        X[column] = X[column].fillna("")

    return X, df[TARGET_COLUMN]


def build_model() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median"))]), NUMERIC_FEATURES),
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                CATEGORICAL_FEATURES,
            ),
            ("skills_text", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=1200), "skills"),
            (
                "skill_levels_text",
                TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=1200),
                "skill_levels",
            ),
            ("interests_text", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=500), "interests"),
            (
                "certifications_text",
                TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=600),
                "certifications",
            ),
        ]
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", LinearSVC(C=1.0, random_state=RANDOM_STATE)),
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

    model = build_model()
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

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        {
            "model": model,
            "label_encoder": label_encoder,
            "features": X.columns.tolist(),
            "target_column": TARGET_COLUMN,
        },
        MODEL_PATH,
    )

    metrics = {
        "model": "Linear SVM 50K Career Classifier",
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

    print("Model: Linear SVM 50K Career Classifier")
    print(f"Dataset: {DATASET_PATH.name}")
    print(f"Target column: {TARGET_COLUMN}")
    print(f"Rows used: {len(X)}")
    print(f"Features used: {X.shape[1]}")
    print(f"Training rows: {len(X_train)}")
    print(f"Testing rows: {len(X_test)}")
    print(f"Career classes: {len(label_encoder.classes_)}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Saved model: {MODEL_PATH}")
    print(f"Saved metrics: {METRICS_PATH}")


if __name__ == "__main__":
    main()
