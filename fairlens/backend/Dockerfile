FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

# ✅ FIXED PATH
COPY backend/requirements/base.txt /app/requirements/

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements/base.txt

# ✅ FIXED COPY
COPY backend /app/

EXPOSE 8000

RUN chmod +x /app/entrypoint.sh