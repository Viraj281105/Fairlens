"""Phase 2.5 Reliability Testing Suite - Test Utilities"""
import subprocess
import time
import logging
from typing import Optional, Dict, Any
import os
import signal

logger = logging.getLogger(__name__)


class DockerContainerManager:
    """Manages Docker containers for failure simulation."""
    
    @staticmethod
    def get_container_id(container_name: str) -> Optional[str]:
        """Get container ID by name."""
        try:
            result = subprocess.run(
                ["docker", "ps", "-aqf", f"name={container_name}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() if result.stdout.strip() else None
        except Exception as e:
            logger.error(f"Failed to get container ID for {container_name}: {e}")
            return None

    @staticmethod
    def stop_container(container_name: str, timeout: int = 10) -> bool:
        """Stop a container gracefully."""
        try:
            subprocess.run(
                ["docker", "stop", "-t", str(timeout), container_name],
                capture_output=True,
                timeout=timeout + 5
            )
            logger.info(f"Stopped container: {container_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop container {container_name}: {e}")
            return False

    @staticmethod
    def start_container(container_name: str) -> bool:
        """Start a stopped container."""
        try:
            subprocess.run(
                ["docker", "start", container_name],
                capture_output=True,
                timeout=30
            )
            logger.info(f"Started container: {container_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to start container {container_name}: {e}")
            return False

    @staticmethod
    def kill_container(container_name: str) -> bool:
        """Forcefully kill a container (simulates crash)."""
        try:
            subprocess.run(
                ["docker", "kill", container_name],
                capture_output=True,
                timeout=10
            )
            logger.info(f"Killed container: {container_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to kill container {container_name}: {e}")
            return False

    @staticmethod
    def restart_container(container_name: str) -> bool:
        """Restart a container."""
        try:
            subprocess.run(
                ["docker", "restart", container_name],
                capture_output=True,
                timeout=30
            )
            logger.info(f"Restarted container: {container_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to restart container {container_name}: {e}")
            return False

    @staticmethod
    def is_container_running(container_name: str) -> bool:
        """Check if a container is currently running."""
        try:
            result = subprocess.run(
                ["docker", "ps", "-f", f"name={container_name}", "--format={{.Status}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return "Up" in result.stdout
        except Exception as e:
            logger.error(f"Failed to check container status: {e}")
            return False

    @staticmethod
    def wait_for_container(container_name: str, timeout: int = 30) -> bool:
        """Wait for a container to start."""
        start = time.time()
        while time.time() - start < timeout:
            if DockerContainerManager.is_container_running(container_name):
                return True
            time.sleep(0.5)
        return False

    @staticmethod
    def get_container_logs(container_name: str, tail: int = 100) -> str:
        """Get recent logs from a container."""
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", str(tail), container_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout
        except Exception as e:
            logger.error(f"Failed to get logs for {container_name}: {e}")
            return ""


class RedisClient:
    """Simple Redis operations for health checks."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._client = None

    @property
    def client(self):
        """Lazy-load redis client."""
        if self._client is None:
            import redis
            self._client = redis.from_url(self.redis_url)
        return self._client

    def is_healthy(self) -> bool:
        """Check if Redis is responding."""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    def clear_all(self):
        """Clear all Redis data (for testing)."""
        try:
            self.client.flushdb()
            logger.info("Cleared all Redis data")
            return True
        except Exception as e:
            logger.error(f"Failed to clear Redis: {e}")
            return False

    def get_task_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task state from Redis."""
        try:
            key = f"celery-task-meta-{task_id}"
            data = self.client.get(key)
            if data:
                import json
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get task state: {e}")
            return None
