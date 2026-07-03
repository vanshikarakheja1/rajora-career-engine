from fastapi.testclient import TestClient

from career_engine.api.main import app, allowed_origins_from_env, cors_credentials_enabled
from career_engine.api.schemas import ChatMessage
from career_engine.services.assistant import MAX_HISTORY_MESSAGES, recent_history


client = TestClient(app)


def sample_profile() -> dict[str, object]:
    return {
        "education_level": "B.Tech",
        "branch": "Computer Science",
        "specialization": "Machine Learning",
        "cgpa": 8.2,
        "class_10_percentage": 85,
        "class_12_percentage": 82,
        "total_certifications": 2,
        "total_projects": 3,
        "internship_count": 1,
        "hackathons": 1,
        "leetcode_questions": 120,
        "github_repositories": 6,
        "expected_salary_lpa": 8,
        "preferred_work_mode": "Hybrid",
        "career_goal": "Data Scientist",
        "certifications": ["Machine Learning Certificate"],
        "skills": ["python", "sql", "machine_learning", "data_analysis", "git", "communication"],
        "interests": ["ai", "data_science"],
    }


def test_health_check() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_recommend_returns_ranked_paths() -> None:
    response = client.post("/api/recommend", json=sample_profile())

    assert response.status_code == 200
    recommendations = response.json()["recommendations"]
    assert len(recommendations) == 5
    assert set(recommendations[0]) == {"career", "match_score", "matched_skills", "missing_skills", "roadmap"}
    assert 0 <= recommendations[0]["match_score"] <= 1


def test_chat_fallback_without_recommendations() -> None:
    response = client.post("/api/chat", json={"message": "What should I do next?"})

    assert response.status_code == 200
    assert "recommendation result" in response.json()["answer"]


def test_invalid_profile_input_returns_validation_error() -> None:
    payload = sample_profile()
    payload["cgpa"] = 12

    response = client.post("/api/recommend", json=payload)

    assert response.status_code == 422


def test_allowed_origins_are_environment_driven(monkeypatch) -> None:
    monkeypatch.setenv("CAREER_ENGINE_ALLOWED_ORIGINS", "https://example.com, http://localhost:8000")

    assert allowed_origins_from_env() == ["https://example.com", "http://localhost:8000"]


def test_wildcard_cors_disables_credentials() -> None:
    assert cors_credentials_enabled(["*"]) is False


def test_recent_history_is_capped() -> None:
    history = [
        ChatMessage(role="user" if index % 2 == 0 else "assistant", content=f"message {index}")
        for index in range(20)
    ]

    capped = recent_history(history)

    assert len(capped) == MAX_HISTORY_MESSAGES
    assert capped[0].content == "message 12"
    assert capped[-1].content == "message 19"
