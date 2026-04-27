import pytest
from unittest.mock import patch
import redis.exceptions

def test_start_audit_redis_down(api_client):
    # Simulate Redis connection failure when attempting to trigger Celery task
    with patch("backend.app.main.trigger_audit_pipeline", side_effect=redis.exceptions.ConnectionError("Redis is down")):
        with pytest.raises(redis.exceptions.ConnectionError):
            api_client.post("/audit/start", json={"dataset_id": "test_dataset_123"})
            # In a production setup, we might want to catch this in main.py and return a 503 Service Unavailable
            # For now, asserting it raises the exception properly so it doesn't fail silently.

def test_celery_task_internal_crash(api_client, monkeypatch):
    from backend.app.celery_client import celery_app
    monkeypatch.setattr(celery_app.conf, "task_always_eager", True)
    monkeypatch.setattr(celery_app.conf, "task_eager_propagates", False) # So exception doesn't blow up the API thread
    
    with patch("worker.tasks.orchestrator.ingestion") as mock_ingestion:
        mock_ingestion.ingest_data.side_effect = RuntimeError("Worker crashed on ingestion")
        
        response = api_client.post("/audit/start", json={"dataset_id": "test_dataset_crash"})
        assert response.status_code == 200
        
        task_id = response.json()["task_id"]
        
        status_response = api_client.get(f"/audit/{task_id}")
        assert status_response.status_code == 200
        assert status_response.json()["task_status"] == "FAILURE"
