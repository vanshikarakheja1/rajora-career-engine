import os
import base64
import secrets
import json
import logging
from contextlib import asynccontextmanager
from hmac import compare_digest
from pathlib import Path
from time import monotonic, time
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest, urlopen

from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from career_engine.api.schemas import (
    ChatRequest,
    ChatResponse,
    RecommendationResponse,
    SessionRequest,
    SessionResponse,
    StudentProfileRequest,
)
from career_engine.ml.model import DatasetNotFoundError, get_recommendations, load_career_catalog, load_match_model
from career_engine.services.assistant import answer_question
from career_engine.services.persistence import save_profile_and_recommendations
from career_engine.services.rate_limit import allow_request


logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DEFAULT_ALLOWED_ORIGINS = ["http://127.0.0.1:8000", "http://localhost:8000"]
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()
REQUIRE_AUTH = os.getenv("CAREER_ENGINE_REQUIRE_AUTH", "true").strip().lower() == "true"
CHAT_RATE_LIMIT = int(os.getenv("CAREER_ENGINE_CHAT_RATE_LIMIT", "20"))
CHAT_RATE_WINDOW_SECONDS = int(os.getenv("CAREER_ENGINE_CHAT_RATE_WINDOW_SECONDS", "60"))
SESSION_RATE_LIMIT = int(os.getenv("CAREER_ENGINE_SESSION_RATE_LIMIT", "30"))
SESSION_ME_RATE_LIMIT = int(os.getenv("CAREER_ENGINE_SESSION_ME_RATE_LIMIT", "60"))
RECOMMEND_RATE_LIMIT = int(os.getenv("CAREER_ENGINE_RECOMMEND_RATE_LIMIT", "20"))
API_RATE_WINDOW_SECONDS = int(os.getenv("CAREER_ENGINE_API_RATE_WINDOW_SECONDS", "60"))
AUTH_CACHE_SECONDS = int(os.getenv("CAREER_ENGINE_AUTH_CACHE_SECONDS", "300"))
UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL", "").strip()
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "").strip()
COOKIE_SECURE = os.getenv("CAREER_ENGINE_COOKIE_SECURE", "false").strip().lower() == "true"
COOKIE_SAMESITE = os.getenv("CAREER_ENGINE_COOKIE_SAMESITE", "lax").strip().lower()
ENABLE_DOCS = os.getenv("CAREER_ENGINE_ENABLE_DOCS", "true").strip().lower() == "true"
CSRF_COOKIE_NAME = "ce_csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
auth_token_cache: dict[str, tuple[float, dict[str, object]]] = {}
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; "
        "base-uri 'self'; "
        "object-src 'none'; "
        "frame-ancestors 'none'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self' data:; "
        "connect-src 'self' https://rajora-career-engine.onrender.com https://*.supabase.co; "
        "form-action 'self'; "
        "upgrade-insecure-requests"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
}


def allowed_origins_from_env() -> list[str]:
    origins = os.getenv("CAREER_ENGINE_ALLOWED_ORIGINS")
    if not origins:
        return DEFAULT_ALLOWED_ORIGINS

    return [origin.strip() for origin in origins.split(",") if origin.strip()]


def cors_credentials_enabled(allowed_origins: list[str]) -> bool:
    if "*" in allowed_origins:
        return False

    return os.getenv("CAREER_ENGINE_ALLOW_CREDENTIALS", "false").strip().lower() == "true"


def jwt_payload(token: str) -> dict[str, object]:
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload.encode("ascii")))
    except (IndexError, ValueError, json.JSONDecodeError):
        return {}


def supabase_public_configured() -> bool:
    return bool(SUPABASE_URL.startswith("https://") and SUPABASE_ANON_KEY and jwt_payload(SUPABASE_ANON_KEY).get("role") == "anon")


def verify_token_value(token: str) -> dict[str, object]:
    now = monotonic()
    cached = auth_token_cache.get(token)
    if cached and cached[0] > now:
        return {**cached[1], "_access_token": token}

    request = UrlRequest(
        f"{SUPABASE_URL}/auth/v1/user",
        headers={
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {token}",
        },
    )
    try:
        with urlopen(request, timeout=8) as response:  # nosec B310
            user = json.loads(response.read().decode("utf-8"))
            token_exp = jwt_payload(token).get("exp")
            ttl = AUTH_CACHE_SECONDS
            if isinstance(token_exp, int):
                ttl = max(0, min(ttl, token_exp - int(time())))
            if ttl > 0:
                auth_token_cache[token] = (now + ttl, user)
            return {**user, "_access_token": token}
    except HTTPError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired session.") from exc
    except URLError as exc:
        raise HTTPException(status_code=503, detail="Authentication service unavailable.") from exc


def refresh_supabase_session(refresh_token: str) -> SessionRequest:
    request = UrlRequest(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token",
        data=json.dumps({"refresh_token": refresh_token}).encode("utf-8"),
        headers={
            "apikey": SUPABASE_ANON_KEY,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=8) as response:  # nosec B310
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh session.") from exc
    except URLError as exc:
        raise HTTPException(status_code=503, detail="Authentication service unavailable.") from exc

    expires_at = data.get("expires_at")
    if not isinstance(expires_at, int):
        expires_in = data.get("expires_in")
        expires_at = int(time()) + int(expires_in or 3600)

    return SessionRequest(
        access_token=str(data.get("access_token") or ""),
        refresh_token=str(data.get("refresh_token") or refresh_token),
        expires_at=expires_at,
    )


def verify_supabase_token(
    authorization: str | None = Header(default=None),
    cookie_access_token: str | None = Cookie(default=None, alias="ce_access_token"),
) -> dict[str, object]:
    if not REQUIRE_AUTH:
        return {}
    if not supabase_public_configured():
        raise HTTPException(status_code=503, detail="Authentication is not configured.")

    token = cookie_access_token or ""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required.")

    return verify_token_value(token)


def cookie_max_age(expires_at: int | None) -> int:
    if not expires_at:
        return 3600
    return max(60, min(60 * 60 * 24 * 7, expires_at - int(time())))


def set_csrf_cookie(response: Response, max_age: int = 60 * 60 * 24 * 7) -> str:
    token = secrets.token_urlsafe(32)
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
    )
    return token


def verify_csrf_token(
    request: Request,
    csrf_header: str | None = Header(default=None, alias=CSRF_HEADER_NAME),
) -> None:
    if not REQUIRE_AUTH:
        return

    csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
    if not csrf_cookie or not csrf_header or not compare_digest(csrf_cookie, csrf_header):
        raise HTTPException(status_code=403, detail="Invalid CSRF token.")


def set_session_cookies(response: Response, session: SessionRequest) -> None:
    access_max_age = cookie_max_age(session.expires_at)
    response.set_cookie(
        key="ce_access_token",
        value=session.access_token,
        max_age=access_max_age,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
    )
    if session.refresh_token:
        response.set_cookie(
            key="ce_refresh_token",
            value=session.refresh_token,
            max_age=60 * 60 * 24 * 30,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE,
            path="/",
        )


def clear_session_cookies(response: Response) -> None:
    for key in ["ce_access_token", "ce_refresh_token", CSRF_COOKIE_NAME]:
        response.delete_cookie(key=key, path="/", secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_match_model()
    load_career_catalog()
    yield


app = FastAPI(
    title="Rajora Career Engine",
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs" if ENABLE_DOCS else None,
    redoc_url="/redoc" if ENABLE_DOCS else None,
    openapi_url="/openapi.json" if ENABLE_DOCS else None,
)
allowed_origins = allowed_origins_from_env()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=cors_credentials_enabled(allowed_origins),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", CSRF_HEADER_NAME],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    for header, value in SECURITY_HEADERS.items():
        response.headers.setdefault(header, value)
    return response


def enforce_rate_limit(request: Request, scope: str, limit: int, window_seconds: int, message: str) -> None:
    client_host = request.client.host if request.client else "unknown"
    allowed = allow_request(
        client_key=f"{scope}:{client_host}",
        limit=limit,
        window_seconds=window_seconds,
        upstash_url=UPSTASH_REDIS_REST_URL,
        upstash_token=UPSTASH_REDIS_REST_TOKEN,
    )
    if not allowed:
        raise HTTPException(status_code=429, detail=message)


def enforce_chat_rate_limit(request: Request) -> None:
    enforce_rate_limit(
        request=request,
        scope="chat",
        limit=CHAT_RATE_LIMIT,
        window_seconds=CHAT_RATE_WINDOW_SECONDS,
        message="Too many chat requests. Please try again shortly.",
    )


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/config")
def public_config() -> dict[str, str | bool]:
    configured = supabase_public_configured()
    return {
        "supabase_configured": configured,
        "supabase_url": SUPABASE_URL,
        "supabase_anon_key": SUPABASE_ANON_KEY if configured else "",
    }


@app.post("/api/session", response_model=SessionResponse)
def create_session(session: SessionRequest, response: Response, request: Request) -> SessionResponse:
    enforce_rate_limit(
        request=request,
        scope="session",
        limit=SESSION_RATE_LIMIT,
        window_seconds=API_RATE_WINDOW_SECONDS,
        message="Too many authentication requests. Please try again shortly.",
    )
    if not supabase_public_configured():
        raise HTTPException(status_code=503, detail="Authentication is not configured.")
    verify_token_value(session.access_token)
    set_session_cookies(response, session)
    csrf_token = set_csrf_cookie(response, cookie_max_age(session.expires_at))
    return SessionResponse(authenticated=True, csrf_token=csrf_token)


@app.get("/api/session/me", response_model=SessionResponse)
def session_me(
    response: Response,
    request: Request,
    csrf_token: str | None = Cookie(default=None, alias=CSRF_COOKIE_NAME),
    user: dict[str, object] = Depends(verify_supabase_token),
) -> SessionResponse:
    enforce_rate_limit(
        request=request,
        scope="session-me",
        limit=SESSION_ME_RATE_LIMIT,
        window_seconds=API_RATE_WINDOW_SECONDS,
        message="Too many session checks. Please try again shortly.",
    )
    if REQUIRE_AUTH and not csrf_token:
        csrf_token = set_csrf_cookie(response)
    return SessionResponse(authenticated=bool(user), csrf_token=csrf_token)


@app.post("/api/session/logout", response_model=SessionResponse)
def destroy_session(response: Response, csrf: None = Depends(verify_csrf_token)) -> SessionResponse:
    clear_session_cookies(response)
    return SessionResponse(authenticated=False)


@app.post("/api/session/refresh", response_model=SessionResponse)
def refresh_session(
    response: Response,
    request: Request,
    refresh_token: str | None = Cookie(default=None, alias="ce_refresh_token"),
) -> SessionResponse:
    enforce_rate_limit(
        request=request,
        scope="session-refresh",
        limit=SESSION_RATE_LIMIT,
        window_seconds=API_RATE_WINDOW_SECONDS,
        message="Too many authentication requests. Please try again shortly.",
    )
    if not supabase_public_configured():
        raise HTTPException(status_code=503, detail="Authentication is not configured.")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh session required.")

    session = refresh_supabase_session(refresh_token)
    set_session_cookies(response, session)
    csrf_token = set_csrf_cookie(response, cookie_max_age(session.expires_at))
    return SessionResponse(authenticated=True, csrf_token=csrf_token)


@app.post("/api/recommend", response_model=RecommendationResponse)
def recommend(
    profile: StudentProfileRequest,
    request: Request,
    user: dict[str, object] = Depends(verify_supabase_token),
    csrf: None = Depends(verify_csrf_token),
) -> RecommendationResponse:
    enforce_rate_limit(
        request=request,
        scope="recommend",
        limit=RECOMMEND_RATE_LIMIT,
        window_seconds=API_RATE_WINDOW_SECONDS,
        message="Too many recommendation requests. Please try again shortly.",
    )
    try:
        recommendations = get_recommendations(profile)
    except DatasetNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    saved = save_profile_and_recommendations(
        supabase_url=SUPABASE_URL,
        anon_key=SUPABASE_ANON_KEY,
        user=user,
        profile=profile,
        recommendations=recommendations,
    )
    if not saved:
        logger.warning("Recommendation was generated but was not saved for user_id=%s.", user.get("id", "unknown"))
    return RecommendationResponse(recommendations=recommendations)


@app.post("/api/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    http_request: Request,
    user: dict[str, object] = Depends(verify_supabase_token),
    csrf: None = Depends(verify_csrf_token),
) -> ChatResponse:
    enforce_chat_rate_limit(http_request)
    return ChatResponse(
        answer=answer_question(
            message=request.message,
            profile=request.profile,
            recommendations=request.recommendations,
            history=request.history,
        )
    )


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
