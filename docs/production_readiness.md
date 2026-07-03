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

5. Match score naming
   - The recommendation API now returns `match_score`.
   - The UI displays this as a match score instead of a calibrated confidence probability.

6. Reproducible setup
   - Runtime and development dependencies are pinned in `requirements.txt`.
   - Jupyter, Notebook, and pytest are included so another device can run notebooks and tests.

7. Active model feature schema
   - `src/career_engine/ml/features.py` now contains the active 50K model feature contract.
   - Linear SVM and XGBoost training scripts import this shared schema.

## Environment Variables

Create a local `.env` file when running the assistant with Groq:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
CAREER_ENGINE_ALLOWED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
CAREER_ENGINE_ALLOW_CREDENTIALS=false
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

## Deployment Notes

- Do not commit `.env` files, API keys, local virtual environments, or datasets.
- Keep `data/raw/` ignored unless dataset licensing explicitly allows publishing.
- Use a real production domain in `CAREER_ENGINE_ALLOWED_ORIGINS`.
- Keep `CAREER_ENGINE_ALLOW_CREDENTIALS=false` unless authentication is added and required.
- Treat `match_score` as a ranking score, not as a probability.
