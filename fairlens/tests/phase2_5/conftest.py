"""
Pytest configuration for Phase 2.5 Reliability Testing

Provides fixtures and configuration for load, chaos, and failure recovery tests.
"""
import pytest
import asyncio
import sys
import os
from pathlib import Path

# Add parent directories to path so imports work
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))
sys.path.insert(0, str(PROJECT_ROOT / "worker"))
sys.path.insert(0, str(PROJECT_ROOT / "tests" / "phase2_5"))

# Configure asyncio for pytest
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    """Configure logging for tests."""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )


@pytest.fixture(autouse=True)
def reset_test_state():
    """Reset state before each test if needed."""
    yield
    # Cleanup after test


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "load: mark test as load testing"
    )
    config.addinivalue_line(
        "markers", "recovery: mark test as failure recovery testing"
    )
    config.addinivalue_line(
        "markers", "chaos: mark test as chaos testing"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark async tests."""
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
