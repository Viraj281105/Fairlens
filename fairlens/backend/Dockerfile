FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/base.txt /app/requirements/
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements/base.txt

# Copy the application code
COPY . /app/

# Expose port
EXPOSE 8000

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh
