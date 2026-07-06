# Render Backend + Vercel Frontend Deployment

## 1. Deploy Backend On Render

Before deploying, create the Supabase database tables:

```text
Supabase -> SQL Editor -> run supabase/schema.sql
```

Create a Render web service from this repository.

Use these settings:

```text
Runtime: Python
Build Command: pip install -r requirements.txt
Start Command: PYTHONPATH=src uvicorn career_engine.api.main:app --host 0.0.0.0 --port $PORT
```

Environment variables:

```env
SUPABASE_URL=https://vqcxhtczrxftihwxykvc.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_public_key
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
CAREER_ENGINE_REQUIRE_AUTH=true
CAREER_ENGINE_RELOAD=false
CAREER_ENGINE_ENABLE_DOCS=false
CAREER_ENGINE_ALLOW_CREDENTIALS=true
CAREER_ENGINE_COOKIE_SECURE=true
CAREER_ENGINE_COOKIE_SAMESITE=none
CAREER_ENGINE_ALLOWED_ORIGINS=https://your-vercel-domain.vercel.app
CAREER_ENGINE_CHAT_RATE_LIMIT=20
CAREER_ENGINE_CHAT_RATE_WINDOW_SECONDS=60
CAREER_ENGINE_SESSION_RATE_LIMIT=30
CAREER_ENGINE_SESSION_ME_RATE_LIMIT=60
CAREER_ENGINE_RECOMMEND_RATE_LIMIT=20
CAREER_ENGINE_API_RATE_WINDOW_SECONDS=60
CAREER_ENGINE_AUTH_CACHE_SECONDS=300
```

After deployment, verify:

```text
https://your-render-service.onrender.com/api/health
```

Expected:

```json
{"status":"ok"}
```

## 2. Deploy Frontend On Vercel

Create a Vercel project from this repository.

Use these settings:

```text
Build Command: node scripts/write_frontend_config.mjs
Output Directory: frontend
```

The Vercel build writes `frontend/config.js`. On Vercel, the frontend uses same-origin `/api` routes, and `vercel.json` proxies those requests to Render. This avoids third-party cookie issues on mobile browsers.

Do not set `CAREER_ENGINE_API_URL` on Vercel unless you intentionally want direct browser-to-Render API calls. Direct calls can cause mobile browsers to drop auth cookies.

## 3. Update Supabase URLs

In Supabase:

```text
Authentication -> URL Configuration
```

Set Site URL:

```text
https://your-vercel-domain.vercel.app
```

Add Redirect URLs:

```text
http://127.0.0.1:8000
https://your-vercel-domain.vercel.app
```

For email/password signup, configure one of these Supabase Auth options:

- Production: enable a custom SMTP provider in `Authentication -> Settings -> SMTP Settings` so confirmation emails are delivered to real users.
- Demo/testing: disable `Confirm Email` in `Authentication -> Providers -> Email` if you want users to sign up and login immediately without email confirmation.

For Google provider, make sure Google Cloud OAuth also allows:

```text
Authorized JavaScript origin:
https://your-vercel-domain.vercel.app

Authorized redirect URI:
https://vqcxhtczrxftihwxykvc.supabase.co/auth/v1/callback
```

## 4. Final Production Checks

1. Open the Vercel frontend.
2. Login with Supabase email or Google.
3. Run a recommendation.
4. Ask the assistant a career-related question.
5. Check Supabase `user_profiles` and `recommendation_history` tables for saved rows.
6. Try calling the Render `/api/recommend` endpoint without a token and confirm it returns `401`.
