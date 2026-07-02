from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from career_engine.api.schemas import CareerRecommendation, StudentProfileRequest
from career_engine.services.roadmap import build_recommendation_details, skill_match_score


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = PROJECT_ROOT / "models" / "linear_svm_50k_career_classifier.joblib"


class DatasetNotFoundError(FileNotFoundError):
    pass


@lru_cache(maxsize=1)
def load_model() -> dict[str, object]:
    if not MODEL_PATH.exists():
        raise DatasetNotFoundError(
            f"Trained model not found at {MODEL_PATH}. Run scripts/train_linear_svm_50k_career_model.py first."
        )

    return joblib.load(MODEL_PATH)


def normalize_text(values: list[str]) -> list[str]:
    return [value.strip().lower().replace("_", " ") for value in values if value.strip()]


def format_skill_levels(skills: list[str]) -> str:
    return ",".join(f"{skill}:3" for skill in normalize_text(skills))


def model_scores(model: object, features: pd.DataFrame) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        return np.asarray(model.predict_proba(features)[0], dtype=float)

    scores = np.asarray(model.decision_function(features)[0], dtype=float)
    scores = scores - scores.max()
    exp_scores = np.exp(scores)
    return exp_scores / exp_scores.sum()


def profile_to_features(profile: StudentProfileRequest) -> pd.DataFrame:
    row: dict[str, object] = {
        "education_level": profile.education_level,
        "branch": profile.branch,
        "specialization": profile.specialization or "Not specified",
        "cgpa": profile.cgpa,
        "class_10_percentage": profile.class_10_percentage,
        "class_12_percentage": profile.class_12_percentage,
        "skills": ",".join(normalize_text(profile.skills)),
        "skill_levels": format_skill_levels(profile.skills),
        "interests": ",".join(normalize_text(profile.interests)),
        "certifications": ",".join(normalize_text(profile.certifications)),
        "projects_count": profile.total_projects,
        "internships_count": profile.internship_count,
        "hackathons": profile.hackathons,
        "preferred_work_mode": profile.preferred_work_mode or "Not specified",
        "expected_salary_lpa": profile.expected_salary_lpa,
    }

    artifact = load_model()
    return pd.DataFrame([row], columns=artifact["features"])


def get_recommendations(profile: StudentProfileRequest, limit: int = 5) -> list[CareerRecommendation]:
    artifact = load_model()
    model = artifact["model"]
    label_encoder = artifact["label_encoder"]
    features = profile_to_features(profile)
    probabilities = model_scores(model, features)
    classes = label_encoder.classes_
    recommendations: list[CareerRecommendation] = []
    selected_skills = {skill.strip().lower() for skill in profile.skills}
    selected_interests = {interest.strip().lower() for interest in profile.interests}

    scored_careers = []
    for index, career_name in enumerate(classes):
        career = str(career_name)
        model_score = float(probabilities[index])
        skills_score = skill_match_score(career, selected_skills)
        interest_bonus = 0.12 if selected_interests and skill_match_score(career, selected_interests) > 0 else 0
        combined_score = min(0.98, max(model_score, skills_score * 0.7) + interest_bonus)
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
