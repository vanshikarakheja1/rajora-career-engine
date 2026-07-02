from career_engine.api.schemas import CareerRecommendation, StudentProfileRequest


def words(message: str) -> set[str]:
    return {part.strip(".,!?;:()[]{}").lower() for part in message.split()}


def join_or_empty(values: list[str]) -> str:
    return ", ".join(values) if values else "none yet"


def top_recommendation(recommendations: list[CareerRecommendation]) -> CareerRecommendation | None:
    return recommendations[0] if recommendations else None


def answer_question(
    message: str,
    profile: StudentProfileRequest | None,
    recommendations: list[CareerRecommendation],
) -> str:
    question = message.lower().strip()
    question_words = words(message)
    top = top_recommendation(recommendations)

    if question_words.intersection({"hello", "hi", "hey"}):
        return (
            "Hi. I can help you understand your career recommendations, missing skills, "
            "and what to do next. Run a recommendation first for the most useful answers."
        )

    if not top:
        return (
            "I need your recommendation result before I can explain a career path deeply. "
            "Fill the profile form, select your skills and interests, then click Recommend Careers."
        )

    if any(word in question for word in ["why", "reason", "recommended", "suggested"]):
        return (
            f"The system ranked {top.career} highest because your profile matched these skills: "
            f"{join_or_empty(top.matched_skills)}. The main gaps are: {join_or_empty(top.missing_skills)}. "
            "The score combines the trained 50K student career model with skill-fit logic."
        )

    if any(word in question for word in ["skill", "missing", "gap", "learn"]):
        return (
            f"For {top.career}, focus first on: {join_or_empty(top.missing_skills[:4])}. "
            "Start with the foundation roadmap, then build one portfolio project that proves those skills."
        )

    if any(word in question for word in ["roadmap", "path", "steps", "plan"]):
        steps = []
        for step in top.roadmap:
            steps.append(f"{step.title}: {' '.join(step.actions)}")
        return f"Roadmap for {top.career}: " + " ".join(steps)

    if any(word in question for word in ["best", "top", "career"]):
        careers = ", ".join(item.career for item in recommendations[:5])
        return f"Your current top career paths are: {careers}. The strongest current match is {top.career}."

    if any(word in question for word in ["profile", "my skills", "about me"]) and profile:
        return (
            f"Your profile shows education in {profile.education_level} / {profile.branch}, "
            f"skills like {join_or_empty(profile.skills)}, and interests like {join_or_empty(profile.interests)}."
        )

    return (
        f"Based on the current recommendation, {top.career} is the strongest path. "
        f"You already match {join_or_empty(top.matched_skills)} and should improve "
        f"{join_or_empty(top.missing_skills)}. Ask me why it was recommended, what to learn, "
        "or what roadmap to follow."
    )
