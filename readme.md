Optimizing tool selection...# FairLens — Distributed AI/ML Audit Pipeline

```markdown
# FairLens

> Scalable, asynchronous AI/ML audit pipeline for bias detection, fairness analysis, and model governance.

---

## 📋 Overview

FairLens is a distributed system designed to audit machine learning models for bias, unfairness, and intersectional disparities. Using a microservices architecture with asynchronous task processing, it enables organizations to scale bias detection and fairness analysis across large datasets without blocking operations.

The system processes complex ML audits as background jobs, tracks progress in real-time, and delivers detailed fairness reports—all through a clean, modern web interface.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                         │
│                  http://localhost:3000                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
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
         │                   │                   │
         ▼                   ▼                   ▼
    ┌─────────┐         ┌─────────┐         ┌─────────┐
    │ Worker 1│         │ Worker 2│         │ Worker N│
    │ Celery  │         │ Celery  │         │ Celery  │
    └────┬────┘         └────┬────┘         └────┬────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                    ┌────────▼────────┐
                    │ Pipeline Engine │
                    │ • Bias Detection│
                    │ • Metrics       │
                    │ • Reports       │
                    └─────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend API** | FastAPI | RESTful service for task submission & status polling |
| **Async Processing** | Celery | Distributed task queue for ML audit jobs |
| **Message Broker** | Redis | Job queueing and inter-service communication |
| **Frontend** | Next.js + TypeScript | Modern UI for data upload and result visualization |
| **Orchestration** | Docker Compose | Multi-container deployment & networking |
| **Monitoring** | Flower (optional) | Real-time worker & task dashboard |

---

## ✨ Key Features

- **Asynchronous Task Processing** — Submit long-running ML audits without blocking the API
- **Real-Time Status Tracking** — Track task lifecycle: PENDING → STARTED → SUCCESS/FAILURE
- **Distributed Architecture** — Scale workers horizontally; Redis brokers all job requests
- **Clean API Design** — Standardized JSON responses with consistent error handling
- **Failure-Safe Handling** — Graceful error recovery; no silent failures or data loss
- **Production-Ready Deployment** — Fully Dockerized; ready for local and cloud environments
- **Comprehensive Testing** — Load, recovery, chaos, and idempotency test suites included
- **Observability** — Optional Flower dashboard for worker metrics and task inspection

---

## 🔄 How It Works

### Step-by-Step Flow

1. **User Uploads Data** — Frontend sends dataset to `/upload` endpoint
2. **Task Created** — Backend creates Celery task and returns `task_id`
3. **Job Queued** — Redis stores task in queue; workers begin processing
4. **Processing Starts** — Worker pulls task, runs ML audit pipeline
5. **Real-Time Polling** — Frontend polls `/status/{task_id}` to track progress
6. **Result Delivered** — Upon completion, user retrieves fairness metrics and report via `/result/{task_id}`

### Status Lifecycle

```
PENDING → STARTED → (RETRY) → SUCCESS
                     └─────→ FAILURE
```

---

## 🚀 Getting Started

### Prerequisites

- **Docker** & **Docker Compose** installed
- **Git** (for cloning)
- Minimum 2GB RAM available

### Run the Project

```bash
# Navigate to infrastructure directory
cd fairlens/infra

# Start all services (builds & deploys)
docker compose up --build

# Services will be ready in ~30 seconds
```

### Access Services

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Web UI for uploads & results |
| **Backend API** | http://localhost:8000 | REST API endpoint |
| **API Docs** | http://localhost:8000/docs | Interactive Swagger documentation |
| **Flower** | http://localhost:5555 | Worker dashboard (optional) |

### Health Check

```bash
curl http://localhost:8000/health
# Response: {"status": "healthy", "services": {...}}
```

---

## 📡 API Endpoints

### POST `/upload`
Submit a dataset for fairness audit.

**Request:**
```json
{
  "file": "<binary data>",
  "model_name": "credit_risk_model",
  "protected_attributes": ["age", "gender", "race"]
}
```

**Response (202 Accepted):**
```json
{
  "task_id": "abc-123-def",
  "status": "PENDING",
  "message": "Audit job queued successfully"
}
```

---

### GET `/status/{task_id}`
Check audit progress in real-time.

**Response:**
```json
{
  "task_id": "abc-123-def",
  "status": "STARTED",
  "progress": 45,
  "current_stage": "Computing fairness metrics",
  "estimated_time_remaining": "~2 minutes"
}
```

**Status Values:**
- `PENDING` — Waiting in queue
- `STARTED` — Worker actively processing
- `SUCCESS` — Audit complete; results ready
- `FAILURE` — Error during processing (with reason)
- `RETRY` — Automatic retry in progress

---

### GET `/result/{task_id}`
Retrieve completed audit results.

**Response (200 OK):**
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

### GET `/health`
System health check.

**Response:**
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

## 📊 Demo Flow

1. **Open** http://localhost:3000
2. **Upload** a CSV dataset with ML predictions
3. **Select** protected attributes (age, gender, race, etc.)
4. **Submit** → Get `task_id`
5. **Watch** real-time progress bar
6. **View** fairness metrics and bias report
7. **Export** as PDF or JSON

---

## 🧪 Testing & Reliability

### Test Suites Included

- **Load Testing** (`test_load.py`) — Handles 100+ concurrent audits
- **Recovery Testing** (`test_recovery.py`) — Verifies graceful restart & data persistence
- **Chaos Testing** (`test_chaos.py`) — Simulates worker failures and network issues
- **Idempotency Testing** (`test_idempotency.py`) — Ensures duplicate submissions are safe

### Run Tests

```bash
# All tests
./scripts/run_tests.sh

# Specific suite
pytest tests/phase2_5/test_load.py -v

# With coverage report
pytest tests/ --cov=fairlens/backend/app
```

---

## 📁 Project Structure

```
fairlens/
├── backend/                # FastAPI application
│   ├── app/
│   │   ├── main.py         # API routes
│   │   ├── celery_client.py
│   │   └── pipeline/       # ML audit pipeline
│   ├── requirements/       # Dependencies
│   └── Dockerfile
│
├── frontend/               # Next.js web UI
│   ├── src/app/           # React components
│   ├── package.json
│   └── Dockerfile
│
├── worker/                 # Celery worker service
│   ├── celery_app.py
│   ├── tasks/
│   │   └── orchestrator.py # Job orchestration
│   └── Dockerfile
│
├── infra/
│   └── docker-compose.yml  # Multi-service orchestration
│
└── tests/                  # Comprehensive test suite
    ├── api/
    ├── e2e/
    ├── phase2_5/          # Reliability tests
    └── worker/
```

---

## 🔮 Future Improvements

- **Advanced Retry Strategies** — Exponential backoff with configurable policies
- **Queue Monitoring Dashboard** — Real-time queue depth and worker utilization metrics
- **Cloud Deployment** — Pre-configured Azure Container Instances / AWS ECS templates
- **Enhanced Observability** — Prometheus metrics, Grafana dashboards, structured logging
- **Batch Processing** — Optimize for large-scale, multi-dataset audits
- **Custom Metrics** — User-defined fairness metrics beyond baseline set
- **Model Versioning** — Track audit results across model iterations

---

## 📝 Notes

- **Data Privacy** — All datasets processed locally; no data sent to external services
- **Scalability** — Add workers via `docker compose up --scale worker=5`
- **Configuration** — Edit `.env` files in `infra/` for custom settings
- **Logs** — View worker logs: `docker logs <worker_container_id>`

---

## 🙌 Contributing

Found a bug? Have an improvement? Open an issue or submit a pull request.

---

## 📄 License

This project is part of the Google Solution Challenge 2026.

---

**Made for fairness. Built for scale.**
```
</markdown></markdown>You've used 77% of your session rate limit. Your session rate limit will reset on April 28 at 2:15 PM. [Learn More](https://aka.ms/github-copilot-rate-limit-error)