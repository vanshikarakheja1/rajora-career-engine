# Rajora Career Engine

Smart Career Recommendation Engine for Indian students using machine learning.

This repository is the starter structure for an internship project. The goal is to build an end-to-end ML system that recommends suitable career paths based on a student's skills, interests, education, certifications, and goals.

## Problem Statement

Many Indian students enter college or the job market without clear career direction. Existing platforms often recommend jobs or careers through keyword matching, but they usually do not understand the full student profile.

The system should understand:

- Skills
- Interests
- Education level
- Academic stream
- Certifications
- Career goals
- Missing skills

The problem is to create an intelligent recommendation engine that suggests suitable careers and gives practical next steps for improvement.

## Solution

The proposed solution is a machine learning based career recommendation engine.

The system will:

- Collect or generate student profile data.
- Map student profiles to career paths.
- Clean and preprocess the data.
- Engineer features from skills, interests, education, certifications, and goals.
- Train and compare multiple ML models.
- Recommend the top 5 career paths.
- Show match scores for recommendations.
- Identify missing skills for each career.
- Explain model decisions using explainability tools.
- Collect user feedback for future retraining.
- Generate a career report for each student.

## Key Features

- Data collection and preprocessing pipeline
- Exploratory data analysis in Jupyter Notebook
- Feature engineering for student profiles
- ML model training and comparison
- Career recommendation output
- Skill gap analysis
- Explainable recommendations
- Feedback loop
- PDF report generation
- Simple frontend form
- REST API for recommendations

## Tech Stack

| Area | Planned Tools |
| --- | --- |
| Language | Python 3.11+ |
| Notebook | Jupyter Notebook |
| Data Analysis | Pandas, NumPy |
| Machine Learning | scikit-learn, XGBoost |
| Explainability | SHAP or LIME |
| API | FastAPI, Uvicorn |
| Frontend | HTML/CSS initially, React optional later |
| Database | SQLite initially, PostgreSQL optional later |
| Model Storage | Pickle or Joblib |
| Reports | ReportLab or similar PDF library |
| Testing | Pytest |
| Version Control | Git and GitHub |

## Datasets

The project will explore the following sources:

### 1. O*NET Online

Website: https://www.onetonline.org/

Purpose:

- Career roles
- Required skills
- Abilities
- Work activities
- Occupation details

### 2. Kaggle Career Datasets

Website: https://www.kaggle.com/

Suggested search terms:

- `career recommendation dataset`
- `student career dataset`
- `skills jobs dataset`
- `career prediction dataset`

Purpose:

- Student profile data
- Career labels
- Skills and education information
- Recommendation target data

### 3. Synthetic Dataset

If public datasets are incomplete, a synthetic dataset can be created using documented rules.

Possible fields:

- Student ID
- Skills
- Interests
- Education level
- Stream
- Certifications
- Career goals
- Recommended career
- Required skills
- Missing skills

Synthetic data generation must be documented clearly so the model methodology remains understandable.

## Expected Input

Example student profile:

```json
{
  "skills": ["python", "statistics", "communication"],
  "interests": ["data", "analytics"],
  "education_level": "B.Tech",
  "stream": "Computer Science",
  "certifications": ["Machine Learning"],
  "career_goals": ["data scientist"]
}
```

## Expected Output

Example recommendation output:

```json
{
  "recommendations": [
    {
      "career": "Data Scientist",
      "match_score": 0.82,
      "matched_skills": ["python", "statistics"],
      "missing_skills": ["machine learning", "sql"],
      "reason": "The student profile strongly matches analytical and programming requirements."
    }
  ]
}
```

## Project Structure

```text
.
|-- data/
|   |-- raw/                 # Original datasets
|   |-- interim/             # Intermediate cleaned datasets
|   `-- processed/           # Final ML-ready datasets
|-- docs/                    # Documentation and architecture notes
|-- frontend/                # Frontend application files
|-- models/                  # Trained model files
|-- notebooks/               # EDA and experiment notebooks
|-- reports/
|   `-- figures/             # Charts and report images
|-- scripts/                 # Utility and training scripts
|-- src/
|   `-- career_engine/
|       |-- api/             # API code
|       |-- data/            # Data processing code
|       |-- ml/              # ML training and inference code
|       |-- services/        # Recommendation and skill-gap services
|       `-- utils/           # Shared helper functions
|-- tests/                   # Test files
|-- .gitignore
|-- requirements.txt
`-- README.md
```

## Local Environment Setup

Python 3.11+ should be used for this project.

The virtual environment should be kept outside the project folder. On this machine, the virtual environment path is:

```powershell
C:\Users\GS\.virtualenvs\rajora-career-engine
```

Create the virtual environment:

```powershell
mkdir $env:USERPROFILE\.virtualenvs
py -3.11 -m venv $env:USERPROFILE\.virtualenvs\rajora-career-engine
```

Activate it:

```powershell
& $env:USERPROFILE\.virtualenvs\rajora-career-engine\Scripts\Activate.ps1
```

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Install dependencies:

```powershell
python -m pip install -r requirements-dev.txt
```

Use `requirements.txt` for production deployment and `requirements-dev.txt` for local notebooks, tests, and training scripts.

Run automated tests:

```powershell
python -m pytest
```

Start Jupyter Notebook:

```powershell
jupyter notebook
```

## Baseline Model

The first baseline model is a simple Decision Tree classifier.

Current baseline setup:

- Dataset: `data/raw/students_5000.xlsx`
- Target column: `recommended_career_1`
- Model: Decision Tree Classifier
- Train/test split: 80/20
- Metric: Accuracy

Run the baseline:

```powershell
python scripts/train_baseline_decision_tree.py
```

Latest local result:

```text
Accuracy: 0.9430
```

## 50K Model Training Results

The newer model training uses `data/raw/student_profiles_50k.csv`.

Dataset summary:

- Rows: 50,000
- Target column: `career_goal`
- Career classes: 24
- Training rows: 40,000
- Testing rows: 10,000

Model comparison:

| Model | Dataset | Target | Accuracy | Macro F1 | Weighted F1 |
| --- | --- | --- | --- | --- | --- |
| Decision Tree Baseline | `students_5000.xlsx` | `recommended_career_1` | 0.9430 | 0.8500 approx | 0.9400 approx |
| XGBoost 50K Classifier | `student_profiles_50k.csv` | `career_goal` | 0.8669 | 0.8665 | 0.8666 |
| Linear SVM 50K Classifier | `student_profiles_50k.csv` | `career_goal` | 0.8724 | 0.8721 | 0.8723 |

These models are kept as comparison models. The active recommender now uses the newer career match-score regressor because it ranks many career paths instead of classifying the user into one software-focused label.

Train the 50K models:

```powershell
python scripts/train_xgboost_50k_career_model.py
python scripts/train_linear_svm_50k_career_model.py
```

The comparison model artifact is:

```text
models/linear_svm_50k_career_classifier.joblib
```

## Active Model: Career Match Score Regressor

The active recommendation model is designed to recommend careers for students and experienced users across many domains. It predicts a `match_score` for each user-career pair instead of classifying a user into one career.

Expected raw files:

```text
data/raw/user_profiles.csv
data/raw/career_catalog.csv
data/raw/career_matches.csv
```

Train it after those files are added locally:

```powershell
python scripts/train_career_match_score_model.py
```

Output artifacts:

```text
models/career_match_score_regressor.joblib
reports/career_match_score_metrics.json
```

Latest result:

| Metric | Value |
| --- | ---: |
| Rows used | 1,149,719 |
| Training rows | 919,855 |
| Testing rows | 229,864 |
| RMSE | 0.0399 |
| MAE | 0.0194 |
| R2 Score | 0.9833 |
| Precision@5 | 0.7987 |

The API uses this model first. If the artifact or career catalog is missing, it falls back to the Linear SVM model.
The committed model artifact includes a small career catalog snapshot for inference, so raw training datasets are not required in GitHub.

## Interactive App

The project now includes a simple user interface for students to enter their profile and get career recommendations.

The app provides:

- Student profile form
- Skill search, custom skill adding, and interest selection
- Career path predictions
- Match score for each recommendation
- Matched skills
- Missing skills
- Roadmap steps to improve toward each career
- Assistant/chatbot for recommendation questions

Run the app:

```powershell
python run_app.py
```

Open:

```text
http://127.0.0.1:8000
```

If the terminal says `uvicorn is not installed`, activate the project virtual environment or run:

```powershell
python -m pip install -r requirements-dev.txt
```

Docker option:

```powershell
docker build -t rajora-career-engine .
docker run --env-file .env -p 8000:8000 rajora-career-engine
```

For Render backend + Vercel frontend deployment, use [docs/deployment.md](docs/deployment.md).

## Supabase Authentication Setup

The app uses Supabase Auth for email/password signup, login, and Google OAuth. Passwords are stored by Supabase, not by this project.

1. In Supabase, open your project.
2. Go to `Project Settings` -> `API`.
3. Copy:
   - Project URL
   - anon public key
4. Create or update `.env`:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_public_key
```

5. Go to `Authentication` -> `URL Configuration`.
6. Set Site URL for local testing:

```text
http://127.0.0.1:8000
```

7. Add this Redirect URL:

```text
http://127.0.0.1:8000
```

8. For Google login, go to `Authentication` -> `Providers` -> `Google`, enable it, and add your Google Client ID and Client Secret. Google must also allow the Supabase callback URL shown on that provider page.

API endpoint used by the UI:

```text
POST /api/recommend
POST /api/chat
```

The assistant can answer basic questions about:

- Why a career was recommended
- Which skills are missing
- What roadmap to follow
- Which career path is the strongest match
- How the user's profile relates to the recommendation

Recommendation scores are returned as `match_score`. This is a hybrid ranking score from the trained model plus rule-based skill and interest fit. It should be treated as a career match score, not as a calibrated probability.

## Production Readiness Updates

The latest code hardening pass fixed the main review findings before deployment:

- Frontend recommendation cards now render dynamic API data using DOM text nodes instead of `innerHTML`.
- API tests cover health, recommendations, chat fallback, invalid input, CORS config, and chat history limits.
- The active match-score model loads from the committed model artifact and no longer requires ignored raw datasets at runtime.
- The API validates string lengths, list sizes, numeric upper bounds, and experienced-user profile fields.
- Chat history is passed to the assistant and capped so long sessions do not overload the API.
- CORS is controlled through environment variables and restricted to the required methods and headers.
- Chat, recommendation, and session endpoints have configurable rate limits for public testing.
- The response field is now `match_score` to avoid presenting the hybrid ranking score as calibrated probability.
- Production dependencies are pinned in `requirements.txt`; notebook, test, and training tools are pinned in `requirements-dev.txt`.
- Model feature constants now match the active 50K Linear SVM/XGBoost training schema.
- Docker and GitHub Actions CI files are included for reproducible deployment checks.

See `docs/production_readiness.md` for the checklist and validation commands.

## Groq Assistant Setup

The recommendation assistant supports two modes:

- Rule-based fallback mode when no Groq key is configured.
- Groq-powered mode for deeper career-path conversations.

Create a local `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_public_key
CAREER_ENGINE_API_URL=https://your-render-service.onrender.com
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

`.env` is ignored by Git and should never be committed.

For deployment, replace `CAREER_ENGINE_ALLOWED_ORIGINS` with the real frontend domain. Avoid using `*` in production. If `*` is used for temporary testing, credentials are automatically disabled by the API configuration.
Keep `CAREER_ENGINE_REQUIRE_AUTH=true` for deployment so recommendation and chat APIs require a valid Supabase session.
Set `CAREER_ENGINE_ENABLE_DOCS=false` on public deployments if you do not want Swagger/OpenAPI exposed.
On Vercel, leave `CAREER_ENGINE_API_URL` unset unless direct browser-to-Render calls are required. The default same-origin `/api` proxy avoids mobile browsers blocking authentication cookies.

The Groq assistant is restricted to:

- User profile discussion
- Career recommendations
- Skill gaps
- Learning roadmap
- Portfolio projects
- Internships and entry-level preparation
- Questions about how the recommendation system works

For unrelated questions, it should politely redirect the user back to career guidance.

## Development Roadmap

| Week | Goal |
| --- | --- |
| Week 1 | Research datasets, define feature set, set up repository structure |
| Week 2 | Build data pipeline and create EDA notebook |
| Week 3 | Perform feature engineering and create train/test split |
| Week 4 | Train and compare at least 3 ML models |
| Week 5 | Build FastAPI recommendation endpoint |
| Week 6 | Add explainability, skill gap logic, and frontend form |
| Week 7 | Add feedback collection and PDF report generation |
| Week 8 | Final testing, documentation, deployment, and demo |

## Model Plan

At least three models should be trained and compared:

- Decision Tree or Logistic Regression as a baseline
- Random Forest
- XGBoost
- Linear SVM for text-heavy skill and interest data
- Optional neural network if the dataset supports it

Evaluation metrics:

- Accuracy
- Precision
- Recall
- F1 score
- Confusion matrix
- Model comparison table

## API Plan

Planned endpoints:

```text
GET /health
POST /recommend
POST /feedback
POST /report
```

`POST /recommend` will accept a student profile and return the top 5 career recommendations.

## Security Notes

- Do not commit `.env` files.
- Do not commit API keys.
- Do not commit private student data.
- Do not commit large datasets unless allowed by license.
- Keep local virtual environments outside the repository.

## Final Deliverables

- Public GitHub repository
- Clean project structure
- EDA notebook
- Dataset documentation
- Trained ML model
- Model evaluation report
- FastAPI recommendation endpoint
- Skill gap analysis
- Explainability output
- PDF report generation
- README with setup and project details
- Demo through frontend, Swagger, Postman, or screen recording

## Current Status

- Project folder structure created.
- README created with complete project information.
- Virtual environment created outside the project folder.
- EDA notebook created.
- Baseline Decision Tree model created.
- Interactive UI and recommendation API created.
- 50K XGBoost and Linear SVM models trained.
- Career match-score regressor trained and wired into the recommendation engine.
- Recommendation assistant/chatbot added.
- Production readiness fixes added for safer frontend rendering, CORS, chat history, tests, pinned dependencies, and active model feature constants.
