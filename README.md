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
- Show confidence scores for recommendations.
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
      "confidence": 0.82,
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
python -m pip install -r requirements.txt
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

The active recommender uses the **Linear SVM 50K Career Classifier** because it performed best on the larger text-heavy dataset.

Train the 50K models:

```powershell
python scripts/train_xgboost_50k_career_model.py
python scripts/train_linear_svm_50k_career_model.py
```

The active model artifact is:

```text
models/linear_svm_50k_career_classifier.joblib
```

## Interactive App

The project now includes a simple user interface for students to enter their profile and get career recommendations.

The app provides:

- Student profile form
- Skill and interest selection
- Career path predictions
- Confidence score for each recommendation
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
- Linear SVM 50K model wired into the recommendation engine.
- Recommendation assistant/chatbot added.
