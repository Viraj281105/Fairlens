from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid

import logging
from .celery_client import celery_app
import redis
import os

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

def trigger_audit_pipeline(job_id: str, dataset_id: str):
    """Triggers the Celery task by name."""
    task = celery_app.send_task("tasks.orchestrator.run_full_audit_pipeline", args=[job_id, dataset_id])
    logger.info(f"[JOB={job_id}] TASK_QUEUED: task_id={task.id}, dataset_id={dataset_id}")
    return task.id


app = FastAPI(
    title="FairLens API",
    description="Bias Auditing & Fairness Remediation Platform",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AuditStartRequest(BaseModel):
    dataset_id: str

@app.get("/health")
def health_check():
    health_status = {"status": "healthy", "redis": "unknown"}
    try:
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        r.ping()
        health_status["redis"] = "connected"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status["redis"] = "disconnected"
        health_status["status"] = "degraded"
    return health_status

@app.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    # Stub: Upload to GCS and register in Firestore
    dataset_id = str(uuid.uuid4())
    return {"message": "Upload successful", "dataset_id": dataset_id, "filename": file.filename}

@app.post("/audit/start")
async def start_audit(request: AuditStartRequest):
    job_id = str(uuid.uuid4())
    logger.info(f"Starting audit for dataset {request.dataset_id}, assigning job {job_id}")
    # Trigger async celery worker
    task_id = trigger_audit_pipeline(job_id, request.dataset_id)
    return {"message": "Audit started", "job_id": job_id, "task_id": task_id}

@app.get("/audit/{job_id}")
def get_audit_status(job_id: str):
    # In this phase, we map job_id -> task_id or assume job_id is task_id if passed.
    # For now, let's just query Celery for any AsyncResult using the provided ID.
    # Ideally, job_id would map to a task_id in Redis/Firestore.
    from celery.result import AsyncResult
    res = AsyncResult(job_id, app=celery_app)
    return {
        "job_id": job_id,
        "task_status": res.status,
        "result": res.result if res.ready() else None
    }

@app.get("/report/{job_id}")
def get_audit_report(job_id: str):
    # Stub: Fetch final report from Firestore
    return {"job_id": job_id, "report": {"fairness_score": 0.85, "issues_found": 2}}

@app.post("/debias/download")
def download_debiased_dataset(job_id: str):
    # Stub: Return URL or stream of debiased dataset from GCS
    return {"job_id": job_id, "download_url": "https://storage.googleapis.com/..."}
