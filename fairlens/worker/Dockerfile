FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

# Assuming backend requirements covers worker dependencies
COPY ../backend/requirements/base.txt /app/requirements/
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements/base.txt

COPY . /app/
# Pipeline logic will be volume mounted or copied in production

CMD ["celery", "-A", "celery_app.app", "worker", "--loglevel=info"]
