# FairLens

> Scalable, asynchronous AI/ML audit pipeline for bias detection, fairness analysis, and model governance.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](infra/docker-compose.yml)
[![Google Solution Challenge](https://img.shields.io/badge/Google%20Solution%20Challenge-2026-orange.svg)](https://developers.google.com/community/gdsc-solution-challenge)

---

## Overview

FairLens is a distributed system designed to audit machine learning models for bias, unfairness, and intersectional disparities. Using a microservices architecture with asynchronous task processing, it enables organizations to scale bias detection and fairness analysis across large datasets without blocking operations.

The system processes complex ML audits as background jobs, tracks progress in real-time, and delivers detailed fairness reports — all through a clean, modern web interface.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                         │
│                  http://localhost:3000                          │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                               │
│              http://localhost:8000/docs                         │
│  • Task Management  • Status Tracking  • Result Retrieval       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Redis Broker   │
                    │ (Message Queue) │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
    ┌─────────┐         ┌─────────┐         ┌─────────┐
    │ Worker 1│         │ Worker 2│         │ Worker N│
    │ Celery  │         │ Celery  │         │ Celery  │
    └────┬────┘         └────┬────┘         └────┬────┘
         └───────────────────┼───────────────────┘
                             │
                    ┌────────▼────────┐
                    │ Pipeline Engine │
                    │ • Bias Detection│
                    │ • Fairness Calc │
                    │ • Report Gen    │
                    └─────────────────┘
```

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend API | FastAPI | RESTful service for task submission & status polling |
| Async Processing | Celery | Distributed task queue for ML audit jobs |
| Message Broker | Redis | Job queueing and inter-service communication |
| Frontend | Next.js + TypeScript | Modern UI for data upload and result visualization |
| Orchestration | Docker Compose | Multi-container deployment & networking |
| Monitoring | Flower (optional) | Real-time worker & task dashboard |

---

## Key Features

- **Asynchronous Task Processing** — Submit long-running ML audits without blocking the API
- **Real-Time Status Tracking** — Track task lifecycle: `PENDING → STARTED → SUCCESS/FAILURE`
- **Distributed Architecture** — Scale workers horizontally; Redis brokers all job requests
- **Clean API Design** — Standardized JSON responses with consistent error handling
- **Failure-Safe Handling** — Graceful error recovery; no silent failures or data loss
- **Production-Ready Deployment** — Fully Dockerized; ready for local and cloud environments
- **Comprehensive Testing** — Load, recovery, chaos, and idempotency test suites included
- **Observability** — Optional Flower dashboard for worker metrics and task inspection

---

## How It Works

### Request lifecycle

1. **Upload** — Frontend sends dataset to `/upload` endpoint
2. **Queue** — Backend creates a Celery task and returns a `task_id`; Redis stores the job
3. **Process** — A worker pulls the task and runs the full ML audit pipeline
4. **Poll** — Frontend polls `/status/{task_id}` to track progress in real time
5. **Retrieve** — On completion, results are fetched via `/result/{task_id}`

### Status lifecycle

```
PENDING → STARTED → SUCCESS
                  └──(RETRY)──→ FAILURE
```

| Status | Meaning |
|--------|---------|
| `PENDING` | Waiting in queue |
| `STARTED` | Worker actively processing |
| `SUCCESS` | Audit complete; results ready |
| `FAILURE` | Error during processing (reason included) |
| `RETRY` | Automatic retry in progress |

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Git
- Minimum 2 GB RAM

### Run

```bash
# Clone and navigate to the infra directory
cd fairlens/infra

# Build and start all services (~30 seconds)
docker compose up --build
```

### Services

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Web UI for uploads & results |
| Backend API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Interactive Swagger docs |
| Flower | http://localhost:5555 | Worker dashboard (optional) |

### Health check

```bash
curl http://localhost:8000/health
# {"status": "healthy", "services": {"api": "up", "redis": "up", "workers": 3}}
```

---

## API Reference

### `POST /upload`

Submit a dataset for fairness audit.

**Request body**
```json
{
  "file": "<binary data>",
  "model_name": "credit_risk_model",
  "protected_attributes": ["age", "gender", "race"]
}
```

**Response — 202 Accepted**
```json
{
  "task_id": "abc-123-def",
  "status": "PENDING",
  "message": "Audit job queued successfully"
}
```

---

### `GET /status/{task_id}`

Check audit progress in real time.

```json
{
  "task_id": "abc-123-def",
  "status": "STARTED",
  "progress": 45,
  "current_stage": "Computing fairness metrics",
  "estimated_time_remaining": "~2 minutes"
}
```

---

### `GET /result/{task_id}`

Retrieve completed audit results.

```json
{
  "task_id": "abc-123-def",
  "status": "SUCCESS",
  "fairness_metrics": {
    "demographic_parity": 0.92,
    "equalized_odds": 0.88,
    "calibration": 0.95
  },
  "bias_summary": "Moderate gender bias detected in approval decisions.",
  "report_url": "/reports/abc-123-def.pdf"
}
```

---

### `GET /health`

System health check.

```json
{
  "status": "healthy",
  "services": {
    "api": "up",
    "redis": "up",
    "workers": 3
  }
}
```

---

## Demo

1. Open http://localhost:3000
2. Upload a CSV with ML predictions
3. Select protected attributes (age, gender, race, etc.)
4. Submit → receive a `task_id`
5. Watch the real-time progress bar
6. View fairness metrics and bias report
7. Export as PDF or JSON

---

## Testing

| Suite | File | Coverage |
|-------|------|----------|
| Load testing | `test_load.py` | 100+ concurrent audits |
| Recovery testing | `test_recovery.py` | Graceful restart & data persistence |
| Chaos testing | `test_chaos.py` | Worker failures & network issues |
| Idempotency testing | `test_idempotency.py` | Safe duplicate submissions |

```bash
# Run all tests
./scripts/run_tests.sh

# Run a specific suite
pytest tests/phase2_5/test_load.py -v

# With coverage report
pytest tests/ --cov=fairlens/backend/app
```

---

## Project Structure

```
fairlens/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── main.py          # API routes
│   │   ├── celery_client.py
│   │   └── pipeline/        # ML audit pipeline
│   ├── requirements/
│   └── Dockerfile
│
├── frontend/                # Next.js web UI
│   ├── src/app/             # React components
│   ├── package.json
│   └── Dockerfile
│
├── worker/                  # Celery worker service
│   ├── celery_app.py
│   ├── tasks/
│   │   └── orchestrator.py  # Job orchestration
│   └── Dockerfile
│
├── infra/
│   └── docker-compose.yml   # Multi-service orchestration
│
└── tests/
    ├── api/
    ├── e2e/
    ├── phase2_5/            # Reliability test suites
    └── worker/
```

---

## Scaling

```bash
# Scale to 5 workers
docker compose up --scale worker=5
```

---

## Roadmap

- [ ] Exponential backoff with configurable retry policies
- [ ] Real-time queue depth and worker utilization dashboard
- [ ] Azure Container Instances / AWS ECS deployment templates
- [ ] Prometheus metrics + Grafana dashboards + structured logging
- [ ] Batch processing for large-scale, multi-dataset audits
- [ ] User-defined fairness metrics beyond the baseline set
- [ ] Model versioning — track audit results across iterations

---

## Notes

- **Data privacy** — All datasets are processed locally; no data is sent to external services.
- **Configuration** — Edit `.env` files in `infra/` for custom settings.
- **Logs** — `docker logs <worker_container_id>`

---

## Contributing

Found a bug or have an improvement? Open an issue or submit a pull request.

---

## License

This project is part of the **Google Solution Challenge 2026**.

---

*Made for fairness. Built for scale.*
