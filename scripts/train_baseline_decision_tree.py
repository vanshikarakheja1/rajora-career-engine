from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_DATASET = DATA_DIR / "students_5000.xlsx"
TARGET_COLUMN = "recommended_career_1"
RANDOM_STATE = 42


def find_dataset() -> Path:
    if DEFAULT_DATASET.exists():
        return DEFAULT_DATASET

    excel_files = sorted(DATA_DIR.glob("*.xlsx"), key=lambda path: path.stat().st_size, reverse=True)
    if not excel_files:
        raise FileNotFoundError(f"No Excel datasets found in {DATA_DIR}")

    return excel_files[0]


def load_dataset(path: Path) -> pd.DataFrame:
    return pd.read_excel(path)


def remove_leakage_columns(df: pd.DataFrame, target_column: str) -> pd.DataFrame:
    # These fields are generated after recommendation, so using them would leak the answer.
    leakage_prefixes = (
        "recommended_career_",
        "career1_confidence",
        "career2_confidence",
        "career3_confidence",
        "career4_confidence",
        "career5_confidence",
        "missing_skill_",
        "recommended_course_",
    )
    leakage_columns = {
        "student_id",
        "final_job_title",
        "company_type",
        "salary_lpa",
        "job_satisfaction",
        "employment_status",
    }

    columns_to_drop = [
        column
        for column in df.columns
        if column == target_column
        or column.startswith("Unnamed:")
        or column.startswith(leakage_prefixes)
        or column in leakage_columns
    ]

    return df.drop(columns=columns_to_drop, errors="ignore")


def build_model(numeric_features: list[str], categorical_features: list[str]) -> Pipeline:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_features),
            ("categorical", categorical_pipeline, categorical_features),
        ]
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", DecisionTreeClassifier(random_state=RANDOM_STATE)),
        ]
    )


def main() -> None:
    dataset_path = find_dataset()
    df = load_dataset(dataset_path)

    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' was not found in {dataset_path.name}")

    df = df.dropna(subset=[TARGET_COLUMN])
    y = df[TARGET_COLUMN]
    X = remove_leakage_columns(df, TARGET_COLUMN)

    numeric_features = X.select_dtypes(include=["number", "bool"]).columns.tolist()
    categorical_features = X.select_dtypes(exclude=["number", "bool"]).columns.tolist()

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    model = build_model(numeric_features, categorical_features)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)

    print("Baseline Model: Decision Tree Classifier")
    print(f"Dataset: {dataset_path.name}")
    print(f"Target column: {TARGET_COLUMN}")
    print(f"Rows used: {len(df)}")
    print(f"Features used: {X.shape[1]}")
    print(f"Training rows: {len(X_train)}")
    print(f"Testing rows: {len(X_test)}")
    print("\nClass distribution:")
    print(y.value_counts().to_string())
    print(f"\nAccuracy: {accuracy:.4f}")
    print("\nClassification report:")
    print(classification_report(y_test, predictions))


if __name__ == "__main__":
    main()
