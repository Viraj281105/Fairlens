$ErrorActionPreference = "Stop"

Write-Host "Starting tests execution for FairLens..."

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RootDir = Split-Path -Parent $ScriptDir
Set-Location $RootDir

Write-Host "Running tests in a disposable Docker container..."
docker run --rm `
    -v "$($RootDir):/app" `
    -w /app `
    python:3.11-slim `
    /bin/bash -c "pip install -r backend/requirements/base.txt && pip install -r backend/requirements/test.txt && export PYTHONPATH=/app && pytest tests/ -v"

Write-Host "Tests completed successfully."
