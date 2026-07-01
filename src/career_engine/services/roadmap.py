from career_engine.api.schemas import RoadmapStep


CAREER_SKILLS: dict[str, list[str]] = {
    "Data Scientist": ["python", "statistics", "sql", "machine_learning", "data_analysis", "tableau"],
    "Cloud Engineer": ["linux", "aws", "docker", "networking", "git"],
    "Full Stack Developer": ["html", "css", "javascript", "react", "nodejs", "sql", "git"],
    "Security Analyst": ["linux", "networking", "cybersecurity", "problem_solving"],
    "Android Developer": ["java", "kotlin", "mobile_development", "git"],
    "Machine Learning Engineer": ["python", "machine_learning", "deep_learning", "tensorflow", "pytorch"],
    "Research Scientist": ["python", "research", "statistics", "machine_learning", "critical_thinking"],
    "FinTech Developer": ["python", "sql", "finance", "security", "problem_solving"],
}

COURSE_HINTS: dict[str, str] = {
    "aws": "Complete AWS Cloud Practitioner basics and deploy one small cloud project.",
    "cybersecurity": "Study security fundamentals, OWASP basics, and common attack patterns.",
    "data_analysis": "Practice data cleaning, EDA, and dashboard building with real datasets.",
    "deep_learning": "Build one neural network project using TensorFlow or PyTorch.",
    "docker": "Containerize a Python or Node.js project and run it locally.",
    "git": "Use Git branches, commits, pull requests, and GitHub project workflows.",
    "html": "Build responsive pages with semantic HTML.",
    "javascript": "Practice DOM handling, async requests, and form validation.",
    "linux": "Learn terminal commands, permissions, processes, and shell basics.",
    "machine_learning": "Train classification and regression models with scikit-learn.",
    "nodejs": "Build REST APIs and connect them with a database.",
    "python": "Practice Python fundamentals, functions, OOP, and data structures.",
    "react": "Build a component-based frontend with forms and API calls.",
    "sql": "Practice joins, grouping, filtering, and schema design.",
    "statistics": "Study probability, distributions, hypothesis testing, and evaluation metrics.",
    "tableau": "Create dashboards that explain trends and comparisons clearly.",
}


def format_skill(skill: str) -> str:
    return skill.replace("_", " ").title()


def skill_match_score(career: str, selected_skills: set[str]) -> float:
    required_skills = CAREER_SKILLS.get(career, [])
    if not required_skills:
        return 0.0

    matched_count = sum(1 for skill in required_skills if skill in selected_skills)
    return matched_count / len(required_skills)


def build_recommendation_details(career: str, selected_skills: set[str]) -> dict[str, object]:
    required_skills = CAREER_SKILLS.get(career, [])
    matched_skills = [skill for skill in required_skills if skill in selected_skills]
    missing_skills = [skill for skill in required_skills if skill not in selected_skills]

    roadmap = [
        RoadmapStep(
            title="Strengthen the foundation",
            actions=[
                COURSE_HINTS.get(skill, f"Build a strong foundation in {format_skill(skill)}.")
                for skill in missing_skills[:3]
            ]
            or ["Keep improving your current core skills with small weekly projects."],
        ),
        RoadmapStep(
            title="Build proof of work",
            actions=[
                f"Create one portfolio project related to {career}.",
                "Write a short README explaining the problem, approach, and result.",
            ],
        ),
        RoadmapStep(
            title="Prepare for opportunities",
            actions=[
                "Update your resume with measurable project outcomes.",
                "Practice interview questions for the role and apply to internships or entry-level roles.",
            ],
        ),
    ]

    return {
        "matched_skills": [format_skill(skill) for skill in matched_skills],
        "missing_skills": [format_skill(skill) for skill in missing_skills],
        "roadmap": roadmap,
    }
