from functools import lru_cache
from pathlib import Path
import re

import joblib
import numpy as np
import pandas as pd

from career_engine.api.schemas import CareerRecommendation, RoadmapStep, StudentProfileRequest
from career_engine.services.roadmap import COURSE_HINTS, build_recommendation_details, format_skill, skill_match_score


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = PROJECT_ROOT / "models" / "linear_svm_50k_career_classifier.joblib"
MATCH_MODEL_PATH = PROJECT_ROOT / "models" / "career_match_score_regressor.joblib"
CAREER_CATALOG_PATH = PROJECT_ROOT / "data" / "raw" / "career_catalog.csv"


class DatasetNotFoundError(FileNotFoundError):
    pass


@lru_cache(maxsize=1)
def load_model() -> dict[str, object]:
    if not MODEL_PATH.exists():
        raise DatasetNotFoundError(
            f"Trained model not found at {MODEL_PATH}. Run scripts/train_linear_svm_50k_career_model.py first."
        )

    return joblib.load(MODEL_PATH)


@lru_cache(maxsize=1)
def load_match_model() -> dict[str, object] | None:
    if not MATCH_MODEL_PATH.exists() or not CAREER_CATALOG_PATH.exists():
        return None

    return joblib.load(MATCH_MODEL_PATH)


@lru_cache(maxsize=1)
def load_career_catalog() -> pd.DataFrame | None:
    artifact = load_match_model()
    if artifact and "career_catalog" in artifact:
        return pd.DataFrame(artifact["career_catalog"]).fillna("")

    if not CAREER_CATALOG_PATH.exists():
        return None

    return pd.read_csv(CAREER_CATALOG_PATH).fillna("")


def normalize_text(values: list[str]) -> list[str]:
    return [value.strip().lower().replace("_", " ") for value in values if value.strip()]


def normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def tokenize_list(value: object) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []

    return [normalize_token(item) for item in str(value).split(",") if normalize_token(item)]


def tokenize_text(value: object) -> set[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return set()

    return {normalize_token(token) for token in re.split(r"[^a-zA-Z0-9]+", str(value)) if normalize_token(token)}


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


def overlap_score(left: set[str], right: set[str]) -> float:
    if not right:
        return 0.0

    return len(left.intersection(right)) / len(right)


def education_score(profile: StudentProfileRequest, education_paths: object) -> float:
    education = normalize_token(profile.education_level)
    branch = normalize_token(profile.branch)
    paths = set(tokenize_list(education_paths))

    if not paths:
        return 0.5
    if education in paths or branch in paths:
        return 1.0
    if any(token in path for path in paths for token in [education, branch] if token):
        return 0.75

    return 0.35


def experience_score(profile: StudentProfileRequest, career_level: object) -> float:
    experience = max(profile.internship_count, profile.total_projects // 3)
    level = str(career_level).lower()

    if "entry" in level or "beginner" in level:
        return 0.85
    if "mid" in level:
        return 0.65 if experience >= 1 else 0.45
    if "senior" in level:
        return 0.45 if experience >= 2 else 0.25

    return 0.6


def career_row_skills(row: pd.Series) -> set[str]:
    return set(
        tokenize_list(row.get("required_skills"))
        + tokenize_list(row.get("preferred_skills"))
        + tokenize_list(row.get("soft_skills"))
    )


def profile_domain(profile: StudentProfileRequest) -> str:
    text = " ".join(normalize_text([profile.branch, profile.specialization or "", profile.career_goal or ""]))
    if any(term in text for term in ["commerce", "business", "management", "finance"]):
        return "Management"
    if any(term in text for term in ["design", "arts", "media"]):
        return "Design"
    if any(term in text for term in ["medical", "health", "nursing"]):
        return "Healthcare"
    if any(term in text for term in ["law", "legal"]):
        return "Law"

    return "Technology"


def match_model_features(profile: StudentProfileRequest, catalog: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    selected_skills = {normalize_token(skill) for skill in profile.skills if normalize_token(skill)}
    selected_interests = {normalize_token(interest) for interest in profile.interests if normalize_token(interest)}
    goal_terms = tokenize_text(profile.career_goal) | tokenize_text(profile.specialization)
    preferred_domain_label = profile_domain(profile)
    preferred_domain = normalize_token(preferred_domain_label)
    rows: list[dict[str, object]] = []
    details: list[dict[str, object]] = []

    for _, career in catalog.iterrows():
        required_skills = set(tokenize_list(career.get("required_skills")))
        preferred_skills = set(tokenize_list(career.get("preferred_skills")))
        soft_skills = set(tokenize_list(career.get("soft_skills")))
        all_skills = required_skills | preferred_skills | soft_skills
        interests = set(tokenize_list(career.get("career_domain"))) | set(tokenize_list(career.get("industry")))
        matched = selected_skills.intersection(all_skills)
        missing = [skill for skill in required_skills if skill not in selected_skills]
        skill_score = overlap_score(selected_skills, all_skills)
        interest_score = overlap_score(selected_interests, interests)
        edu_score = education_score(profile, career.get("education_paths"))
        exp_score = experience_score(profile, career.get("career_level"))
        goal_score = overlap_score(goal_terms, tokenize_text(career.get("career_title")))
        domain_score = 1.0 if preferred_domain == normalize_token(str(career.get("career_domain"))) else 0.0

        rows.append(
            {
                "age": 21,
                "years_experience": max(profile.internship_count, profile.total_projects // 3),
                "salary_expectation": profile.expected_salary_lpa,
                "skill_match_score": overlap_score(selected_skills, all_skills),
                "interest_match_score": overlap_score(selected_interests, interests),
                "education_match_score": education_score(profile, career.get("education_paths")),
                "experience_match_score": experience_score(profile, career.get("career_level")),
                "user_type": "Student",
                "education_level": profile.education_level,
                "field_of_study": profile.branch,
                "current_role": "Student",
                "preferred_work_style": profile.preferred_work_mode or "Not specified",
                "preferred_domain": preferred_domain_label,
                "location_preference": "India",
                "career_domain": career.get("career_domain"),
                "career_level": career.get("career_level"),
                "industry": career.get("industry"),
            }
        )
        details.append(
            {
                "career": str(career.get("career_title")),
                "matched_skills": sorted(matched),
                "missing_skills": missing,
                "fit_score": (skill_score * 0.45) + (interest_score * 0.2) + (edu_score * 0.2) + (exp_score * 0.15),
                "goal_score": goal_score,
                "domain_score": domain_score,
            }
        )

    return pd.DataFrame(rows), details


def build_catalog_roadmap(career: str, missing_skills: list[str]) -> list[RoadmapStep]:
    first_skills = missing_skills[:3]
    return [
        RoadmapStep(
            title="Strengthen the foundation",
            actions=[
                COURSE_HINTS.get(skill, f"Build a strong foundation in {format_skill(skill)}.")
                for skill in first_skills
            ]
            or ["Keep improving your current core skills with small weekly projects."],
        ),
        RoadmapStep(
            title="Build proof of work",
            actions=[
                f"Create one portfolio project related to {career}.",
                "Document the problem, tools used, result, and skills demonstrated.",
            ],
        ),
        RoadmapStep(
            title="Prepare for opportunities",
            actions=[
                "Update your resume and portfolio with measurable outcomes.",
                "Practice role-specific interview questions and apply to relevant opportunities.",
            ],
        ),
    ]


def get_match_model_recommendations(profile: StudentProfileRequest, limit: int) -> list[CareerRecommendation] | None:
    artifact = load_match_model()
    catalog = load_career_catalog()
    if not artifact or catalog is None:
        return None

    features, details = match_model_features(profile, catalog)
    predictions = np.asarray(artifact["model"].predict(features[artifact["features"]]), dtype=float)
    combined_scores = []
    for index, prediction in enumerate(predictions):
        detail = details[index]
        model_score = float(np.clip(prediction, 0, 1))
        combined_scores.append(
            (model_score * 0.45)
            + (float(detail["fit_score"]) * 0.25)
            + (float(detail["goal_score"]) * 0.2)
            + (float(detail["domain_score"]) * 0.1)
        )
    recommendations: list[CareerRecommendation] = []

    for index in np.argsort(combined_scores)[::-1][:limit]:
        detail = details[int(index)]
        recommendations.append(
            CareerRecommendation(
                career=detail["career"],
                match_score=round(float(np.clip(combined_scores[index], 0, 1)), 4),
                matched_skills=[format_skill(skill) for skill in detail["matched_skills"]],
                missing_skills=[format_skill(skill) for skill in detail["missing_skills"]],
                roadmap=build_catalog_roadmap(detail["career"], detail["missing_skills"]),
            )
        )

    return recommendations


def get_recommendations(profile: StudentProfileRequest, limit: int = 5) -> list[CareerRecommendation]:
    match_recommendations = get_match_model_recommendations(profile, limit)
    if match_recommendations:
        return match_recommendations

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
                match_score=round(float(combined_score), 4),
                matched_skills=details["matched_skills"],
                missing_skills=details["missing_skills"],
                roadmap=details["roadmap"],
            )
        )

    return recommendations
