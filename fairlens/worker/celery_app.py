import os
from celery import Celery

# Fetch Redis URL from environment, defaulting to localhost for dev without docker
redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

app = Celery(
    "fairlens_worker",
    broker=redis_url,
    backend=redis_url,
    include=["tasks.orchestrator"]
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
