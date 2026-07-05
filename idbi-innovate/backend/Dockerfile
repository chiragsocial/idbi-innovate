# FastAPI backend for Hugging Face Spaces (Docker SDK). Serves on port 7860.
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app PYTHONUNBUFFERED=1

# deps first (better layer caching)
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# app code
COPY . /app

# generate synthetic data + train the portable logreg model at build time,
# so the container starts instantly with data + a probability-of-default model
RUN python data/generate.py --n 5000 && python -m ml.train_logreg && python -m ml.fairness

EXPOSE 7860
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
