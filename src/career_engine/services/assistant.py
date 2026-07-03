import logging
import os

from dotenv import load_dotenv
from groq import Groq

from career_engine.api.schemas import CareerRecommendation, ChatMessage, StudentProfileRequest


load_dotenv()

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MAX_HISTORY_MESSAGES = 8
logger = logging.getLogger(__name__)


def words(message: str) -> set[str]:
    return {part.strip(".,!?;:()[]{}").lower() for part in message.split()}


def join_or_empty(values: list[str]) -> str:
    return ", ".join(values) if values else "none yet"


def top_recommendation(recommendations: list[CareerRecommendation]) -> CareerRecommendation | None:
    return recommendations[0] if recommendations else None


def recommendation_context(
    profile: StudentProfileRequest | None,
    recommendations: list[CareerRecommendation],
) -> str:
    profile_text = "No profile was provided."
    if profile:
        profile_text = (
            f"Education: {profile.education_level}, branch: {profile.branch}, "
            f"specialization: {profile.specialization or 'not specified'}, CGPA: {profile.cgpa}, "
            f"skills: {join_or_empty(profile.skills)}, interests: {join_or_empty(profile.interests)}, "
            f"career goal: {profile.career_goal or 'not specified'}."
        )

    recommendation_lines = []
    for item in recommendations[:5]:
        roadmap = "; ".join(
            f"{step.title}: {' '.join(step.actions)}"
            for step in item.roadmap
        )
        recommendation_lines.append(
            f"{item.career} | match_score={item.match_score} | matched={join_or_empty(item.matched_skills)} | "
            f"missing={join_or_empty(item.missing_skills)} | roadmap={roadmap}"
        )

    recommendations_text = "\n".join(recommendation_lines) or "No recommendations available."
    return f"Student profile:\n{profile_text}\n\nRecommendations:\n{recommendations_text}"


def is_career_related(message: str) -> bool:
    allowed_terms = {
        "career",
        "recommendation",
        "recommended",
        "skill",
        "skills",
        "roadmap",
        "learn",
        "project",
        "portfolio",
        "internship",
        "job",
        "profile",
        "education",
        "branch",
        "specialization",
        "salary",
        "resume",
        "interview",
        "path",
        "goal",
        "missing",
        "gap",
        "why",
        "best",
        "compare",
        "next",
    }
    return bool(words(message).intersection(allowed_terms))


def recent_history(history: list[ChatMessage]) -> list[ChatMessage]:
    return history[-MAX_HISTORY_MESSAGES:]


def groq_messages(
    message: str,
    profile: StudentProfileRequest | None,
    recommendations: list[CareerRecommendation],
    history: list[ChatMessage],
) -> list[dict[str, str]]:
    messages = [
        {
            "role": "system",
            "content": (
                "You are the Rajora Career Engine assistant. Answer only about the user's profile, "
                "career recommendations, skill gaps, roadmaps, projects, internships, resumes, "
                "interview preparation, and how this recommendation system works. Be helpful, "
                "specific, and practical for Indian students. If the user asks unrelated questions, "
                "politely refuse and redirect to career guidance. Do not invent model scores or "
                "recommendations beyond the provided context."
            ),
        },
        {
            "role": "user",
            "content": recommendation_context(profile, recommendations),
        },
    ]

    messages.extend(
        {"role": item.role, "content": item.content}
        for item in recent_history(history)
    )
    messages.append({"role": "user", "content": message})
    return messages


def groq_answer(
    message: str,
    profile: StudentProfileRequest | None,
    recommendations: list[CareerRecommendation],
    history: list[ChatMessage],
) -> str | None:
    if not GROQ_API_KEY or not recommendations:
        return None

    if not is_career_related(message):
        return (
            "I can help with career recommendations, skill gaps, roadmaps, profile improvement, "
            "and questions about this system. I cannot answer unrelated topics here."
        )

    try:
        client = Groq(api_key=GROQ_API_KEY, timeout=12.0)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            temperature=0.35,
            max_tokens=650,
            messages=groq_messages(message, profile, recommendations, history),
        )
        return response.choices[0].message.content or None
    except Exception as exc:
        logger.warning("Groq assistant failed: %s", exc)
        return None


def answer_question(
    message: str,
    profile: StudentProfileRequest | None,
    recommendations: list[CareerRecommendation],
    history: list[ChatMessage] | None = None,
) -> str:
    history = history or []
    ai_answer = groq_answer(message, profile, recommendations, history)
    if ai_answer:
        return ai_answer

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
            "The match score combines the trained 50K student career model with skill-fit logic."
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
