FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    CAREER_ENGINE_HOST=0.0.0.0 \
    CAREER_ENGINE_PORT=8000 \
    CAREER_ENGINE_RELOAD=false

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY frontend ./frontend
COPY models ./models
COPY reports ./reports
COPY run_app.py README.md ./

EXPOSE 8000

CMD ["python", "run_app.py"]
