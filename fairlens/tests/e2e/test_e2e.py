import pytest
import time
from unittest.mock import patch
from backend.app.celery_client import celery_app

# Use CELERY_ALWAYS_EAGER to run tasks synchronously during testing
@patch("worker.tasks.orchestrator.ingestion")
@patch("worker.tasks.orchestrator.schema_analysis")
@patch("worker.tasks.orchestrator.protected_attribute_detection")
@patch("worker.tasks.orchestrator.fairness_metrics")
@patch("worker.tasks.orchestrator.intersectional_analysis")
@patch("worker.tasks.orchestrator.counterfactuals")
@patch("worker.tasks.orchestrator.explanation")
@patch("worker.tasks.orchestrator.debiasing")
@patch("worker.tasks.orchestrator.report_generation")
def test_full_pipeline_e2e(
    mock_report, mock_debiasing, mock_explanation, mock_cf, 
    mock_intersection, mock_fairness, mock_protected, mock_schema, mock_ingestion,
    api_client, monkeypatch
):
    # Configure celery to run tasks eagerly (synchronously) for the test
    monkeypatch.setattr(celery_app.conf, "task_always_eager", True)
    monkeypatch.setattr(celery_app.conf, "task_eager_propagates", True)
    
    mock_report.generate_final_report.return_value = {"status": "success"}

    # 1. Trigger the audit
    response = api_client.post("/audit/start", json={"dataset_id": "test_dataset_e2e"})
    assert response.status_code == 200
    data = response.json()
    task_id = data["task_id"]
    job_id = data["job_id"]
    
    # Because task_always_eager is True, the task has already run synchronously!
    
    # 2. Poll for status
    status_response = api_client.get(f"/audit/{task_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    
    # The status should be SUCCESS if task_always_eager is true
    assert status_data["task_status"] == "SUCCESS"
    assert status_data["result"] == {"status": "success"}
