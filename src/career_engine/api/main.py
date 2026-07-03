import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from career_engine.api.schemas import ChatRequest, ChatResponse, RecommendationResponse, StudentProfileRequest
from career_engine.ml.model import DatasetNotFoundError, get_recommendations
from career_engine.services.assistant import answer_question


PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DEFAULT_ALLOWED_ORIGINS = ["http://127.0.0.1:8000", "http://localhost:8000"]


def allowed_origins_from_env() -> list[str]:
    origins = os.getenv("CAREER_ENGINE_ALLOWED_ORIGINS")
    if not origins:
        return DEFAULT_ALLOWED_ORIGINS

    return [origin.strip() for origin in origins.split(",") if origin.strip()]


def cors_credentials_enabled(allowed_origins: list[str]) -> bool:
    if "*" in allowed_origins:
        return False

    return os.getenv("CAREER_ENGINE_ALLOW_CREDENTIALS", "false").strip().lower() == "true"


app = FastAPI(title="Rajora Career Engine", version="0.2.0")
allowed_origins = allowed_origins_from_env()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=cors_credentials_enabled(allowed_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/recommend", response_model=RecommendationResponse)
def recommend(profile: StudentProfileRequest) -> RecommendationResponse:
    try:
        recommendations = get_recommendations(profile)
    except DatasetNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return RecommendationResponse(recommendations=recommendations)


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(
        answer=answer_question(
            message=request.message,
            profile=request.profile,
            recommendations=request.recommendations,
            history=request.history,
        )
    )


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
