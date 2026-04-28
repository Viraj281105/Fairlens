from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Request
from fastapi.responses import JSONResponse
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

def success_response(data: dict = None):
    return {"success": True, "data": data or {}, "error": None}

def error_response(message: str, error_type: str = "Error", status_code: int = 400):
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "data": None, "error": {"message": message, "type": error_type}}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error at {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "data": None, "error": {"message": "Internal server error", "type": type(exc).__name__}}
    )

@app.get("/health")
def health_check():
    health_status = {"status": "ok", "services": {"api": "up", "redis": "down", "worker": "down"}}
    
    # Check Redis
    try:
        redis_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
        r = redis.from_url(redis_url)
        r.ping()
        health_status["services"]["redis"] = "up"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status["status"] = "degraded"
        
    # Check Worker
    try:
        ping_result = celery_app.control.ping(timeout=1.0)
        if ping_result:
            health_status["services"]["worker"] = "up"
        else:
            health_status["status"] = "degraded"
    except Exception as e:
        logger.error(f"Worker health check failed: {e}")
        health_status["status"] = "degraded"
        
    return health_status

@app.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    dataset_id = str(uuid.uuid4())
    logger.info(f"Uploaded file: {file.filename}, dataset_id: {dataset_id}")
    return success_response({"message": "Upload successful", "dataset_id": dataset_id, "filename": file.filename})

@app.post("/audit/start")
async def start_audit(request: AuditStartRequest):
    job_id = str(uuid.uuid4())
    logger.info(f"Starting audit for dataset {request.dataset_id}, assigning job {job_id}")
    task_id = trigger_audit_pipeline(job_id, request.dataset_id)
    return success_response({"message": "Audit started", "job_id": job_id, "task_id": task_id})

@app.get("/status/{task_id}")
def get_audit_status(task_id: str):
    from celery.result import AsyncResult
    res = AsyncResult(task_id, app=celery_app)
    
    data = {
        "task_id": task_id,
        "status": res.status,
    }
    
    if res.status == 'SUCCESS':
        data["result"] = res.result
    elif res.status == 'FAILURE':
        data["error"] = str(res.result)
    elif res.status == 'PROGRESS':
        data["step"] = res.info.get('step', 'Processing') if res.info else 'Processing'
        
    return success_response(data)

@app.get("/audit/{job_id}")
def get_audit_job(job_id: str):
    from celery.result import AsyncResult
    res = AsyncResult(job_id, app=celery_app)
    return success_response({
        "job_id": job_id,
        "task_status": res.status,
        "result": res.result if res.ready() else None
    })

@app.get("/report/{job_id}")
def get_audit_report(job_id: str):
    # Stub: Fetch final report from Firestore
    return success_response({"job_id": job_id, "report": {"fairness_score": 0.85, "issues_found": 2}})

@app.post("/debias/download")
def download_debiased_dataset(job_id: str):
    # Stub: Return URL or stream of debiased dataset from GCS
    return success_response({"job_id": job_id, "download_url": "https://storage.googleapis.com/..."})
