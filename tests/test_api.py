from fastapi.testclient import TestClient

from career_engine.api import main as main_module
from career_engine.api.main import app, allowed_origins_from_env, cors_credentials_enabled, verify_supabase_token
from career_engine.api.schemas import ChatMessage, SessionRequest
from career_engine.ml import model as model_module
from career_engine.services import rate_limit
from career_engine.services.assistant import MAX_HISTORY_MESSAGES, question_category, recent_history


client = TestClient(app)
app.dependency_overrides[verify_supabase_token] = lambda: {"id": "test-user"}


def csrf_headers(token: str = "test-csrf-token") -> dict[str, str]:
    client.cookies.clear()
    client.cookies.set(main_module.CSRF_COOKIE_NAME, token)
    return {main_module.CSRF_HEADER_NAME: token}


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


def test_public_config_shape() -> None:
    response = client.get("/api/config")

    assert response.status_code == 200
    assert set(response.json()) == {"supabase_configured", "supabase_url", "supabase_anon_key"}


def test_security_headers_are_applied() -> None:
    response = client.get("/api/health")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert "camera=()" in response.headers["permissions-policy"]


def test_session_cookie_is_set_and_cleared(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(main_module, "SUPABASE_ANON_KEY", "header.payload.signature")
    monkeypatch.setattr(main_module, "supabase_public_configured", lambda: True)
    monkeypatch.setattr(main_module, "verify_token_value", lambda token: {"id": "test-user", "_access_token": token})

    response = client.post(
        "/api/session",
        json={"access_token": "test-access-token-value", "refresh_token": "test-refresh-token-value", "expires_at": 4102444800},
    )

    assert response.status_code == 200
    assert response.json()["authenticated"] is True
    assert response.json()["csrf_token"]
    assert "ce_access_token" in response.headers["set-cookie"]
    assert main_module.CSRF_COOKIE_NAME in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]

    logout_response = client.post("/api/session/logout", headers=csrf_headers(response.json()["csrf_token"]))

    assert logout_response.status_code == 200
    assert "ce_access_token" in logout_response.headers["set-cookie"]


def test_session_refresh_rotates_cookies(monkeypatch) -> None:
    client.cookies.clear()
    client.cookies.set("ce_refresh_token", "old-refresh-token")
    monkeypatch.setattr(main_module, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(main_module, "SUPABASE_ANON_KEY", "header.payload.signature")
    monkeypatch.setattr(main_module, "supabase_public_configured", lambda: True)
    monkeypatch.setattr(
        main_module,
        "refresh_supabase_session",
        lambda token: SessionRequest(access_token="new-access-token-value", refresh_token="new-refresh-token-value", expires_at=4102444800),
    )

    response = client.post("/api/session/refresh")

    assert response.status_code == 200
    assert response.json()["authenticated"] is True
    assert response.json()["csrf_token"]
    assert "ce_access_token" in response.headers["set-cookie"]
    assert "ce_refresh_token" in response.headers["set-cookie"]


def test_session_refresh_requires_refresh_cookie() -> None:
    client.cookies.clear()

    response = client.post("/api/session/refresh")

    assert response.status_code == 401


def test_recommend_returns_ranked_paths() -> None:
    response = client.post("/api/recommend", json=sample_profile(), headers=csrf_headers())

    assert response.status_code == 200
    recommendations = response.json()["recommendations"]
    assert len(recommendations) == 5
    assert set(recommendations[0]) == {"career", "match_score", "matched_skills", "missing_skills", "roadmap"}
    assert 0 <= recommendations[0]["match_score"] <= 1


def test_recommend_saves_profile_and_recommendations(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(main_module, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(main_module, "SUPABASE_ANON_KEY", "anon")
    def fake_save(**kwargs):
        calls.append(kwargs)
        return True

    monkeypatch.setattr(main_module, "save_profile_and_recommendations", fake_save)

    response = client.post("/api/recommend", json=sample_profile(), headers=csrf_headers())

    assert response.status_code == 200
    assert len(calls) == 1
    assert calls[0]["profile"].education_level == "B.Tech"
    assert len(calls[0]["recommendations"]) == 5


def test_recommend_still_returns_when_persistence_fails(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(main_module, "SUPABASE_ANON_KEY", "anon")
    monkeypatch.setattr(main_module, "save_profile_and_recommendations", lambda **kwargs: False)

    response = client.post("/api/recommend", json=sample_profile(), headers=csrf_headers())

    assert response.status_code == 200
    assert len(response.json()["recommendations"]) == 5


def test_recommend_requires_authentication() -> None:
    app.dependency_overrides.pop(verify_supabase_token, None)
    response = client.post("/api/recommend", json=sample_profile(), headers=csrf_headers())
    app.dependency_overrides[verify_supabase_token] = lambda: {"id": "test-user"}

    assert response.status_code in {401, 503}


def test_recommend_rejects_missing_csrf_token() -> None:
    client.cookies.clear()

    response = client.post("/api/recommend", json=sample_profile())

    assert response.status_code == 403


def test_recommend_rate_limit_blocks_excess(monkeypatch) -> None:
    rate_limit.local_request_log.clear()
    monkeypatch.setattr(main_module, "RECOMMEND_RATE_LIMIT", 1)
    monkeypatch.setattr(main_module, "API_RATE_WINDOW_SECONDS", 60)

    try:
        first_response = client.post("/api/recommend", json=sample_profile(), headers=csrf_headers("recommend-limit"))
        second_response = client.post("/api/recommend", json=sample_profile(), headers=csrf_headers("recommend-limit"))

        assert first_response.status_code == 200
        assert second_response.status_code == 429
    finally:
        rate_limit.local_request_log.clear()


def test_session_rate_limit_blocks_excess(monkeypatch) -> None:
    rate_limit.local_request_log.clear()
    monkeypatch.setattr(main_module, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(main_module, "SUPABASE_ANON_KEY", "header.payload.signature")
    monkeypatch.setattr(main_module, "SESSION_RATE_LIMIT", 1)
    monkeypatch.setattr(main_module, "API_RATE_WINDOW_SECONDS", 60)
    monkeypatch.setattr(main_module, "supabase_public_configured", lambda: True)
    monkeypatch.setattr(main_module, "verify_token_value", lambda token: {"id": "test-user", "_access_token": token})
    payload = {"access_token": "test-access-token-value", "refresh_token": "test-refresh-token-value", "expires_at": 4102444800}

    try:
        first_response = client.post("/api/session", json=payload)
        second_response = client.post("/api/session", json=payload)

        assert first_response.status_code == 200
        assert second_response.status_code == 429
    finally:
        rate_limit.local_request_log.clear()


def test_session_me_rate_limit_blocks_excess(monkeypatch) -> None:
    rate_limit.local_request_log.clear()
    monkeypatch.setattr(main_module, "SESSION_ME_RATE_LIMIT", 1)
    monkeypatch.setattr(main_module, "API_RATE_WINDOW_SECONDS", 60)

    try:
        first_response = client.get("/api/session/me")
        second_response = client.get("/api/session/me")

        assert first_response.status_code == 200
        assert second_response.status_code == 429
    finally:
        rate_limit.local_request_log.clear()


def test_match_model_works_without_raw_catalog(monkeypatch) -> None:
    model_module.load_match_model.cache_clear()
    model_module.load_career_catalog.cache_clear()
    monkeypatch.setattr(model_module, "CAREER_CATALOG_PATH", model_module.PROJECT_ROOT / "data" / "raw" / "missing.csv")
    monkeypatch.setattr(model_module, "load_model", lambda: (_ for _ in ()).throw(AssertionError("fallback model used")))

    recommendations = model_module.get_recommendations(model_module.StudentProfileRequest(**sample_profile()))

    assert len(recommendations) == 5
    model_module.load_match_model.cache_clear()
    model_module.load_career_catalog.cache_clear()


def test_chat_fallback_without_recommendations() -> None:
    response = client.post("/api/chat", json={"message": "What should I do next?"}, headers=csrf_headers())

    assert response.status_code == 200
    assert "recommendation result" in response.json()["answer"]


def test_invalid_profile_input_returns_validation_error() -> None:
    payload = sample_profile()
    payload["cgpa"] = 12

    response = client.post("/api/recommend", json=payload, headers=csrf_headers())

    assert response.status_code == 422


def test_oversized_skill_list_returns_validation_error() -> None:
    payload = sample_profile()
    payload["skills"] = [f"skill-{index}" for index in range(51)]

    response = client.post("/api/recommend", json=payload, headers=csrf_headers())

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


def test_assistant_question_classification() -> None:
    assert question_category("which skills should I learn next") == "career"
    assert question_category("what is the weather today") == "irrelevant"


def test_local_rate_limiter_blocks_after_limit() -> None:
    rate_limit.local_request_log.clear()

    assert rate_limit.allow_request("test-client", limit=2, window_seconds=60)
    assert rate_limit.allow_request("test-client", limit=2, window_seconds=60)
    assert not rate_limit.allow_request("test-client", limit=2, window_seconds=60)


def test_rate_limiter_falls_back_when_shared_store_fails(monkeypatch) -> None:
    rate_limit.local_request_log.clear()
    monkeypatch.setattr(rate_limit, "allow_with_upstash", lambda *args, **kwargs: (_ for _ in ()).throw(TimeoutError()))

    assert rate_limit.allow_request(
        "fallback-client",
        limit=1,
        window_seconds=60,
        upstash_url="https://example.upstash.io",
        upstash_token="token",
    )
    assert not rate_limit.allow_request(
        "fallback-client",
        limit=1,
        window_seconds=60,
        upstash_url="https://example.upstash.io",
        upstash_token="token",
    )
