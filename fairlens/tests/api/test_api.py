import io
from unittest.mock import patch

def test_health_check_healthy(api_client, mock_redis):
    # Mock redis to return ping true
    with patch("backend.app.main.redis.from_url", return_value=mock_redis):
        response = api_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "redis": "connected"}

def test_health_check_degraded(api_client):
    # Simulate redis failure
    with patch("backend.app.main.redis.from_url", side_effect=Exception("Connection refused")):
        response = api_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "degraded", "redis": "disconnected"}

def test_upload_dataset_valid(api_client):
    file_content = b"header1,header2\nval1,val2"
    files = {"file": ("dataset.csv", io.BytesIO(file_content), "text/csv")}
    response = api_client.post("/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Upload successful"
    assert "dataset_id" in data
    assert data["filename"] == "dataset.csv"

def test_upload_dataset_empty(api_client):
    # Fastapi treats no file as a 422 validation error because `file: UploadFile = File(...)` is required
    response = api_client.post("/upload")
    assert response.status_code == 422

@patch("backend.app.main.trigger_audit_pipeline")
def test_start_audit(mock_trigger, api_client):
    mock_trigger.return_value = "mock_task_id"
    response = api_client.post("/audit/start", json={"dataset_id": "test_dataset_123"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Audit started"
    assert "job_id" in data
    assert data["task_id"] == "mock_task_id"
    
    # Assert celery task trigger was called with correct dataset
    mock_trigger.assert_called_once()
    args, kwargs = mock_trigger.call_args
    assert args[1] == "test_dataset_123"
