# Production Readiness Notes

This document tracks the hardening work completed after the code review.

## Fixed Review Findings

1. Frontend rendering safety
   - Recommendation cards, roadmap steps, tags, errors, and checkbox labels are rendered with DOM APIs and `textContent`.
   - The frontend no longer uses `innerHTML`.

2. Automated API tests
   - Tests were added under `tests/`.
   - Coverage includes health check, recommendation response, chat fallback, invalid profile validation, CORS environment parsing, wildcard CORS credential safety, and chat history capping.

3. Chat history handling
   - The frontend caps chat history before sending it to the API.
   - The backend caps assistant context to the latest messages before sending context to Groq.
   - The assistant now receives conversation history for better multi-turn answers.

4. CORS configuration
    - CORS origins are read from `CAREER_ENGINE_ALLOWED_ORIGINS`.
    - Credentials are disabled by default.
    - If a wildcard origin is used for temporary testing, credentials remain disabled.
    - Allowed methods and headers are restricted to the API's current needs.

5. Match score naming
   - The recommendation API now returns `match_score`.
   - The UI displays this as a match score instead of a calibrated confidence probability.

6. Reproducible setup
   - Runtime dependencies are pinned in `requirements.txt`.
   - Notebook, test, and training dependencies are pinned in `requirements-dev.txt`.

7. Active model feature schema
    - `src/career_engine/ml/features.py` now contains the active 50K model feature contract.
    - Linear SVM and XGBoost training scripts import this shared schema.

8. Deployment model loading
   - The active match-score model loads from `models/career_match_score_regressor.joblib`.
   - The committed artifact contains the career catalog snapshot, so raw datasets are not required at runtime.

9. Production safety controls
   - Recommendation payloads now have bounded strings, bounded lists, and numeric upper limits.
   - The API accepts student and experienced-user profile fields.
   - Chat, recommendation, and session endpoints have rate limits for public demos.
   - Docker and GitHub Actions CI files are included.

## Environment Variables

Create a local `.env` file when running the assistant with Groq:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_public_key
CAREER_ENGINE_ALLOWED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
CAREER_ENGINE_ALLOW_CREDENTIALS=false
CAREER_ENGINE_REQUIRE_AUTH=true
CAREER_ENGINE_COOKIE_SECURE=false
CAREER_ENGINE_COOKIE_SAMESITE=lax
CAREER_ENGINE_ENABLE_DOCS=true
CAREER_ENGINE_CHAT_RATE_LIMIT=20
CAREER_ENGINE_CHAT_RATE_WINDOW_SECONDS=60
CAREER_ENGINE_SESSION_RATE_LIMIT=30
CAREER_ENGINE_SESSION_ME_RATE_LIMIT=60
CAREER_ENGINE_RECOMMEND_RATE_LIMIT=20
CAREER_ENGINE_API_RATE_WINDOW_SECONDS=60
CAREER_ENGINE_AUTH_CACHE_SECONDS=300
UPSTASH_REDIS_REST_URL=
UPSTASH_REDIS_REST_TOKEN=
```

For deployment, set `CAREER_ENGINE_ALLOWED_ORIGINS` to the deployed frontend domain.

## Validation Commands

Run these commands from the project root after activating the virtual environment:

```powershell
python -m py_compile run_app.py src\career_engine\api\main.py src\career_engine\api\schemas.py src\career_engine\ml\model.py src\career_engine\ml\features.py src\career_engine\services\assistant.py src\career_engine\services\roadmap.py
python -m pytest
node --check frontend\app.js
python run_app.py
```

Then open:

```text
http://127.0.0.1:8000
```

Docker:

```powershell
docker build -t rajora-career-engine .
docker run --env-file .env -p 8000:8000 rajora-career-engine
```

## Deployment Notes

- Do not commit `.env` files, API keys, local virtual environments, or datasets.
- Use Supabase Auth for credentials. Do not store user passwords in this repository or local storage.
- Keep `data/raw/` ignored unless dataset licensing explicitly allows publishing.
- Use a real production domain in `CAREER_ENGINE_ALLOWED_ORIGINS`.
- Keep `CAREER_ENGINE_ALLOW_CREDENTIALS=false` unless authentication is added and required.
- Keep `CAREER_ENGINE_REQUIRE_AUTH=true` so protected API endpoints reject missing or expired sessions.
- Use `CAREER_ENGINE_ALLOW_CREDENTIALS=true`, `CAREER_ENGINE_COOKIE_SECURE=true`, and `CAREER_ENGINE_COOKIE_SAMESITE=none` when the Vercel frontend calls the Render backend.
- Set `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` for shared API rate limiting across backend instances.
- Set `CAREER_ENGINE_ENABLE_DOCS=false` if Swagger/OpenAPI should not be public.
- Treat `match_score` as a ranking score, not as a probability.
- Do not copy `data/raw/` into Docker images or public repositories.
