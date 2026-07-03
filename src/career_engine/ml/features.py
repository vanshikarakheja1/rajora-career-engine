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

MODEL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES + TEXT_FEATURES
TARGET_COLUMN = "career_goal"
