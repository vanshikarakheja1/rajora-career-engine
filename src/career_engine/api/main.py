from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from career_engine.api.schemas import ChatRequest, ChatResponse, RecommendationResponse, StudentProfileRequest
from career_engine.ml.model import DatasetNotFoundError, get_recommendations
from career_engine.services.assistant import answer_question


PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI(title="Rajora Career Engine", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
        )
    )


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
