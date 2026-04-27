import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
import fakeredis

# Celery test configuration
@pytest.fixture(scope="session")
def celery_config():
    return {
        "broker_url": "memory://",
        "result_backend": "cache+memory://",
        "task_always_eager": True,
        "task_eager_propagates": True,
    }

@pytest.fixture
def api_client():
    """Provides a FastAPI test client."""
    return TestClient(app)

@pytest.fixture
def mock_redis():
    """Provides a fakeredis instance to mock Redis without requiring a server."""
    return fakeredis.FakeRedis()
