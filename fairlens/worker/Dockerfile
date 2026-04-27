FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY backend/requirements/base.txt /app/requirements/

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements/base.txt

# ✅ Copy BOTH backend + worker
COPY backend /app/backend
COPY worker /app/worker

# Move into worker directory for execution
WORKDIR /app/worker

# Create a non-root user to avoid Celery SecurityWarning
RUN groupadd -r celerygroup && useradd -r -g celerygroup celeryuser \
    && chown -R celeryuser:celerygroup /app
USER celeryuser

CMD ["celery", "-A", "celery_app.app", "worker", "--loglevel=info"]