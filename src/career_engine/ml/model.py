from functools import lru_cache
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier

from career_engine.api.schemas import CareerRecommendation, StudentProfileRequest
from career_engine.ml.features import INTEREST_FEATURES, MODEL_FEATURES, SOFT_SKILLS, TECHNICAL_SKILLS
from career_engine.services.roadmap import build_recommendation_details, skill_match_score


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATASET_PATH = PROJECT_ROOT / "data" / "raw" / "students_5000.xlsx"
TARGET_COLUMN = "recommended_career_1"
RANDOM_STATE = 42


class DatasetNotFoundError(FileNotFoundError):
    pass


@lru_cache(maxsize=1)
def load_model() -> Pipeline:
    if not DATASET_PATH.exists():
        raise DatasetNotFoundError(
            f"Dataset not found at {DATASET_PATH}. Add the local dataset before running predictions."
        )

    df = pd.read_excel(DATASET_PATH).dropna(subset=[TARGET_COLUMN])
    available_features = [feature for feature in MODEL_FEATURES if feature in df.columns]
    X = df[available_features]
    y = df[TARGET_COLUMN]

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

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", DecisionTreeClassifier(random_state=RANDOM_STATE)),
        ]
    )
    model.fit(X, y)
    return model


def profile_to_features(profile: StudentProfileRequest) -> pd.DataFrame:
    selected_skills = {skill.strip().lower() for skill in profile.skills}
    selected_interests = {interest.strip().lower() for interest in profile.interests}

    row: dict[str, object] = {
        "education_level": profile.education_level,
        "branch": profile.branch,
        "specialization": profile.specialization or "Not specified",
        "cgpa": profile.cgpa,
        "class_10_percentage": profile.class_10_percentage,
        "class_12_percentage": profile.class_12_percentage,
        "total_certifications": profile.total_certifications,
        "total_projects": profile.total_projects,
        "internship_count": profile.internship_count,
        "hackathons": profile.hackathons,
        "leetcode_questions": profile.leetcode_questions,
        "github_repositories": profile.github_repositories,
        "personality_investigative": 1 if "research" in selected_interests else 0,
        "preferred_work_mode": profile.preferred_work_mode or "Not specified",
        "career_goal": profile.career_goal or "Not specified",
        "expected_salary_lpa": profile.expected_salary_lpa,
    }

    for skill in [*TECHNICAL_SKILLS, *SOFT_SKILLS]:
        row[skill] = 1 if skill in selected_skills else 0

    for interest, feature in INTEREST_FEATURES.items():
        row[feature] = 1 if interest in selected_interests else 0

    return pd.DataFrame([row], columns=MODEL_FEATURES)


def get_recommendations(profile: StudentProfileRequest, limit: int = 5) -> list[CareerRecommendation]:
    model = load_model()
    features = profile_to_features(profile)
    probabilities = model.predict_proba(features)[0]
    classes = model.named_steps["classifier"].classes_
    recommendations: list[CareerRecommendation] = []
    selected_skills = {skill.strip().lower() for skill in profile.skills}

    scored_careers = []
    for index, career_name in enumerate(classes):
        career = str(career_name)
        model_score = float(probabilities[index])
        skills_score = skill_match_score(career, selected_skills)
        combined_score = min(0.95, max(model_score * 0.95, skills_score * 0.85))
        scored_careers.append((combined_score, index, career))

    for combined_score, index, career in sorted(scored_careers, reverse=True)[:limit]:
        details = build_recommendation_details(career, selected_skills)
        recommendations.append(
            CareerRecommendation(
                career=career,
                confidence=round(float(combined_score), 4),
                matched_skills=details["matched_skills"],
                missing_skills=details["missing_skills"],
                roadmap=details["roadmap"],
            )
        )

    return recommendations
