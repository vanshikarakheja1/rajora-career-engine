import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
USER_PROFILES_PATH = RAW_DIR / "user_profiles.csv"
CAREER_CATALOG_PATH = RAW_DIR / "career_catalog.csv"
CAREER_MATCHES_PATH = RAW_DIR / "career_matches.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "career_match_score_regressor.joblib"
METRICS_PATH = PROJECT_ROOT / "reports" / "career_match_score_metrics.json"
TARGET_COLUMN = "match_score"
RANDOM_STATE = 42

NUMERIC_FEATURES = [
    "age",
    "years_experience",
    "salary_expectation",
    "skill_match_score",
    "interest_match_score",
    "education_match_score",
    "experience_match_score",
]

CATEGORICAL_FEATURES = [
    "user_type",
    "education_level",
    "field_of_study",
    "current_role",
    "preferred_work_style",
    "preferred_domain",
    "location_preference",
    "career_domain",
    "career_level",
    "industry",
]

MODEL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")


def load_training_data() -> pd.DataFrame:
    for path in [USER_PROFILES_PATH, CAREER_CATALOG_PATH, CAREER_MATCHES_PATH]:
        require_file(path)

    print("Loading datasets...", flush=True)
    users = pd.read_csv(USER_PROFILES_PATH)
    careers = pd.read_csv(CAREER_CATALOG_PATH)
    matches = pd.read_csv(CAREER_MATCHES_PATH).dropna(subset=[TARGET_COLUMN])

    print("Merging user, career, and match data...", flush=True)
    data = matches.merge(users, on="user_id", how="inner")
    data = data.merge(careers, on="career_id", how="inner", suffixes=("_match", ""))

    for column in MODEL_FEATURES:
        if column not in data.columns:
            data[column] = None

    return data


def split_by_user(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_users, test_users = train_test_split(
        data["user_id"].drop_duplicates(),
        test_size=0.2,
        random_state=RANDOM_STATE,
    )
    return data[data["user_id"].isin(train_users)], data[data["user_id"].isin(test_users)]


def build_model() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                    ]
                ),
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "encoder",
                            OrdinalEncoder(
                                handle_unknown="use_encoded_value",
                                unknown_value=-1,
                                encoded_missing_value=-1,
                            ),
                        ),
                    ]
                ),
                CATEGORICAL_FEATURES,
            ),
        ]
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "regressor",
                HistGradientBoostingRegressor(
                    max_iter=120,
                    learning_rate=0.06,
                    max_leaf_nodes=31,
                    l2_regularization=0.01,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def precision_at_k(frame: pd.DataFrame, k: int = 5) -> float | None:
    if "recommended" not in frame.columns:
        return None

    scores = []
    for _, group in frame.groupby("user_id"):
        top = group.sort_values("predicted_score", ascending=False).head(k)
        scores.append(float(top["recommended"].sum()) / k)

    return sum(scores) / len(scores) if scores else None


def main() -> None:
    data = load_training_data()
    print("Splitting train/test users...", flush=True)
    train_data, test_data = split_by_user(data)

    X_train = train_data[MODEL_FEATURES].copy()
    y_train = train_data[TARGET_COLUMN].astype(float)
    X_test = test_data[MODEL_FEATURES].copy()
    y_test = test_data[TARGET_COLUMN].astype(float)

    model = build_model()
    print("Training score prediction model...", flush=True)
    model.fit(X_train, y_train)

    print("Testing model...", flush=True)
    predictions = model.predict(X_test).clip(0, 1)
    evaluated = test_data[["user_id", "career_id", "career_title", "recommended"]].copy()
    evaluated["predicted_score"] = predictions
    precision_5 = precision_at_k(evaluated, 5)

    metrics = {
        "model": "Histogram Gradient Boosting Career Match Score Regressor",
        "target_column": TARGET_COLUMN,
        "source_datasets": [
            USER_PROFILES_PATH.name,
            CAREER_CATALOG_PATH.name,
            CAREER_MATCHES_PATH.name,
        ],
        "rows_used": int(len(data)),
        "training_rows": int(len(train_data)),
        "testing_rows": int(len(test_data)),
        "features_used": MODEL_FEATURES,
        "rmse": round(float(root_mean_squared_error(y_test, predictions)), 4),
        "mae": round(float(mean_absolute_error(y_test, predictions)), 4),
        "r2": round(float(r2_score(y_test, predictions)), 4),
        "precision_at_5": None if precision_5 is None else round(float(precision_5), 4),
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "features": MODEL_FEATURES,
            "target_column": TARGET_COLUMN,
            "career_catalog": pd.read_csv(CAREER_CATALOG_PATH).fillna("").to_dict(orient="records"),
        },
        MODEL_PATH,
    )
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print("Model: Histogram Gradient Boosting Career Match Score Regressor")
    print(f"Rows used: {len(data)}")
    print(f"RMSE: {metrics['rmse']}")
    print(f"MAE: {metrics['mae']}")
    print(f"R2: {metrics['r2']}")
    print(f"Precision@5: {metrics['precision_at_5']}")
    print(f"Saved model: {MODEL_PATH}")
    print(f"Saved metrics: {METRICS_PATH}")


if __name__ == "__main__":
    main()
