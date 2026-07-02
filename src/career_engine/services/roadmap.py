from career_engine.api.schemas import RoadmapStep


CAREER_SKILLS: dict[str, list[str]] = {
    "Data Scientist": ["python", "statistics", "sql", "machine_learning", "data_analysis", "tableau"],
    "Data Analyst": ["sql", "excel", "statistics", "data_analysis", "power_bi", "tableau"],
    "Cloud Engineer": ["linux", "aws", "docker", "networking", "git"],
    "DevOps Engineer": ["linux", "docker", "kubernetes", "aws", "git", "ci_cd"],
    "Full Stack Developer": ["html", "css", "javascript", "react", "nodejs", "sql", "git"],
    "Software Engineer": ["python", "java", "data_structures", "git", "problem_solving"],
    "Web Developer": ["html", "css", "javascript", "react", "git"],
    "Security Analyst": ["linux", "networking", "cybersecurity", "problem_solving"],
    "Cybersecurity Analyst": ["linux", "networking", "cybersecurity", "risk_analysis", "problem_solving"],
    "Penetration Tester": ["linux", "networking", "cybersecurity", "web_security", "scripting"],
    "Android Developer": ["java", "kotlin", "mobile_development", "git"],
    "Mobile App Developer": ["java", "kotlin", "ios_development", "mobile_development", "git"],
    "Machine Learning Engineer": ["python", "machine_learning", "deep_learning", "tensorflow", "pytorch"],
    "AI Research Scientist": ["python", "research", "machine_learning", "deep_learning", "statistics"],
    "Computer Vision Engineer": ["python", "computer_vision", "opencv", "deep_learning", "pytorch"],
    "NLP Engineer": ["python", "nlp", "machine_learning", "deep_learning", "transformers"],
    "Research Scientist": ["python", "research", "statistics", "machine_learning", "critical_thinking"],
    "FinTech Developer": ["python", "sql", "finance", "security", "problem_solving"],
    "Business Analyst": ["excel", "sql", "business_analytics", "communication", "power_bi"],
    "Product Manager": ["communication", "leadership", "market_research", "analytics", "product_strategy"],
    "UI UX Designer": ["design", "user_research", "figma", "prototyping", "communication"],
    "Game Developer": ["c++", "c#", "unity", "game_development", "problem_solving"],
    "Blockchain Developer": ["blockchain", "solidity", "javascript", "security", "web3"],
    "Embedded Systems Engineer": ["c", "c++", "embedded_systems", "iot", "electronics"],
    "Database Administrator": ["sql", "mysql", "postgresql", "database_design", "linux"],
    "Network Engineer": ["networking", "linux", "security", "troubleshooting", "cloud"],
    "QA Test Engineer": ["testing", "automation", "selenium", "python", "attention_to_detail"],
    "Site Reliability Engineer": ["linux", "cloud", "monitoring", "docker", "scripting"],
}

COURSE_HINTS: dict[str, str] = {
    "aws": "Complete AWS Cloud Practitioner basics and deploy one small cloud project.",
    "automation": "Learn test automation basics and automate one repeatable workflow.",
    "business_analytics": "Practice turning business questions into dashboards and clear recommendations.",
    "cybersecurity": "Study security fundamentals, OWASP basics, and common attack patterns.",
    "data_analysis": "Practice data cleaning, EDA, and dashboard building with real datasets.",
    "data_structures": "Practice arrays, strings, trees, graphs, and complexity analysis.",
    "deep_learning": "Build one neural network project using TensorFlow or PyTorch.",
    "design": "Study visual hierarchy, layout, accessibility, and user-centered design.",
    "docker": "Containerize a Python or Node.js project and run it locally.",
    "git": "Use Git branches, commits, pull requests, and GitHub project workflows.",
    "html": "Build responsive pages with semantic HTML.",
    "javascript": "Practice DOM handling, async requests, and form validation.",
    "linux": "Learn terminal commands, permissions, processes, and shell basics.",
    "machine_learning": "Train classification and regression models with scikit-learn.",
    "monitoring": "Learn logs, metrics, alerts, and uptime monitoring for deployed systems.",
    "networking": "Study IP addressing, DNS, HTTP, routing, firewalls, and troubleshooting.",
    "nodejs": "Build REST APIs and connect them with a database.",
    "python": "Practice Python fundamentals, functions, OOP, and data structures.",
    "react": "Build a component-based frontend with forms and API calls.",
    "sql": "Practice joins, grouping, filtering, and schema design.",
    "statistics": "Study probability, distributions, hypothesis testing, and evaluation metrics.",
    "tableau": "Create dashboards that explain trends and comparisons clearly.",
    "testing": "Learn manual testing, test cases, bug reports, and regression testing.",
    "user_research": "Practice interviewing users and converting findings into design decisions.",
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
