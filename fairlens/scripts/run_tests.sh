#!/bin/bash
set -e

echo "Starting tests execution for FairLens..."

# Ensure we are in the root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

echo "Running tests in a disposable Docker container..."
docker run --rm \
    -v "$ROOT_DIR:/app" \
    -w /app \
    python:3.11-slim \
    /bin/bash -c "\
        pip install -r backend/requirements/base.txt && \
        pip install -r backend/requirements/test.txt && \
        export PYTHONPATH=/app && \
        pytest tests/ -v"

echo "Tests completed successfully."
