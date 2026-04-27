#!/bin/sh

echo "Starting FastAPI server with Uvicorn and Gunicorn..."

# Run migrations here if necessary in the future

# Start Gunicorn with Uvicorn workers
exec gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
