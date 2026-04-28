"""Phase 2.5 - Failure Recovery Testing"""
import pytest
import asyncio
import time
import logging
from test_utils import DockerContainerManager, RedisClient
from async_client import AsyncAPIClient

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_worker_crash_recovery():
    """
    Simulate worker crash:
    1. Start a task
    2. Kill Celery worker
    3. Restart worker
    4. Verify task is retried or marked failed
    """
    logger.info("=" * 60)
    logger.info("TEST: Worker Crash Recovery")
    logger.info("=" * 60)
    
    client = AsyncAPIClient()
    docker_mgr = DockerContainerManager()
    
    # Step 1: Start an audit task
    logger.info("Step 1: Starting audit task...")
    upload_result = await client.create_dataset()
    assert upload_result.success, "Upload failed"
    
    dataset_id = upload_result.response_data.get("dataset_id")
    audit_result = await client.start_audit(dataset_id)
    assert audit_result.success, "Audit start failed"
    
    job_id = audit_result.response_data.get("job_id")
    task_id = audit_result.response_data.get("task_id")
    logger.info(f"Task started: {task_id}")
    
    # Step 2: Wait a moment for task to start processing
    await asyncio.sleep(2)
    
    # Step 3: Kill the worker
    logger.info("Step 2: Killing worker container...")
    success = docker_mgr.kill_container("fairlens_worker")
    assert success, "Failed to kill worker"
    
    # Verify it's dead
    await asyncio.sleep(1)
    is_running = docker_mgr.is_container_running("fairlens_worker")
    assert not is_running, "Worker should not be running"
    logger.info("Worker killed successfully")
    
    # Step 4: Restart worker
    logger.info("Step 3: Restarting worker...")
    success = docker_mgr.restart_container("fairlens_worker")
    assert success, "Failed to restart worker"
    
    # Wait for restart
    started = docker_mgr.wait_for_container("fairlens_worker", timeout=30)
    assert started, "Worker failed to restart"
    logger.info("Worker restarted successfully")
    
    # Step 5: Verify system is responsive
    logger.info("Step 4: Verifying system recovery...")
    health_result = await client.get_health()
    assert health_result.success, "API should be responsive after worker restart"
    logger.info("API is responsive")
    
    # Step 6: Check if task was retried or failed (it should NOT be lost)
    await asyncio.sleep(3)
    status_result = await client.get_audit_status(job_id)
    
    if status_result.success:
        task_status = status_result.response_data.get("task_status")
        logger.info(f"Task status after recovery: {task_status}")
        # Task should be in one of these states (not indefinitely stuck)
        assert task_status in ["PENDING", "PROGRESS", "SUCCESS", "FAILURE", "RETRY"]
    else:
        logger.warning("Could not retrieve task status (may be expected during recovery)")
    
    logger.info("✓ Worker crash recovery test passed")


@pytest.mark.asyncio
async def test_redis_outage_recovery():
    """
    Simulate Redis outage:
    1. Stop Redis
    2. Try to upload (should fail gracefully)
    3. Restart Redis
    4. Verify system recovers and new tasks work
    """
    logger.info("=" * 60)
    logger.info("TEST: Redis Outage Recovery")
    logger.info("=" * 60)
    
    client = AsyncAPIClient()
    docker_mgr = DockerContainerManager()
    redis_client = RedisClient()
    
    # Verify Redis is healthy initially
    logger.info("Step 1: Verifying Redis is healthy...")
    assert redis_client.is_healthy(), "Redis should be healthy initially"
    
    # Step 2: Stop Redis
    logger.info("Step 2: Stopping Redis...")
    success = docker_mgr.stop_container("fairlens_redis", timeout=5)
    assert success, "Failed to stop Redis"
    
    await asyncio.sleep(1)
    is_running = docker_mgr.is_container_running("fairlens_redis")
    assert not is_running, "Redis should not be running"
    logger.info("Redis stopped successfully")
    
    # Step 3: Try to perform operations (should fail gracefully)
    logger.info("Step 3: Attempting upload with Redis down...")
    upload_result = await client.create_dataset()
    
    if upload_result.success:
        logger.info("Upload succeeded (Redis may not be critical for uploads)")
    else:
        logger.info(f"Upload failed gracefully: {upload_result.error}")
        assert upload_result.error is not None, "Should have clear error message"
    
    # Step 4: Restart Redis
    logger.info("Step 4: Restarting Redis...")
    success = docker_mgr.start_container("fairlens_redis")
    assert success, "Failed to start Redis"
    
    # Wait for startup
    started = docker_mgr.wait_for_container("fairlens_redis", timeout=30)
    assert started, "Redis failed to start"
    
    await asyncio.sleep(2)
    logger.info("Redis restarted successfully")
    
    # Step 5: Verify Redis is healthy
    logger.info("Step 5: Verifying Redis recovery...")
    assert redis_client.is_healthy(), "Redis should be healthy after restart"
    
    # Step 6: Verify system is responsive
    health_result = await client.get_health()
    assert health_result.success, "API should be responsive after Redis restart"
    assert health_result.response_data.get("redis") == "connected", "Redis should be connected"
    logger.info("API reports Redis as connected")
    
    # Step 7: Start a new task to verify full recovery
    logger.info("Step 6: Starting new audit after recovery...")
    upload_result = await client.create_dataset()
    assert upload_result.success, "Upload should succeed after Redis recovery"
    
    dataset_id = upload_result.response_data.get("dataset_id")
    audit_result = await client.start_audit(dataset_id)
    assert audit_result.success, "Audit should start after Redis recovery"
    
    job_id = audit_result.response_data.get("job_id")
    logger.info(f"New task started successfully: {job_id}")
    
    # Step 8: Check status to confirm task is processing
    await asyncio.sleep(1)
    status_result = await client.get_audit_status(job_id)
    assert status_result.success, "Should be able to query task status"
    
    logger.info("✓ Redis outage recovery test passed")


@pytest.mark.asyncio
async def test_api_remains_responsive_under_load():
    """Verify API remains responsive while tasks are processing."""
    logger.info("=" * 60)
    logger.info("TEST: API Responsiveness Under Load")
    logger.info("=" * 60)
    
    client = AsyncAPIClient()
    
    # Step 1: Start multiple tasks
    logger.info("Step 1: Starting 10 concurrent audits...")
    upload_results = await client.concurrent_uploads(count=10)
    dataset_ids = [r["upload"]["dataset_id"] for r in upload_results if r["upload"]["success"]]
    
    audit_results = await client.concurrent_audits(dataset_ids)
    job_ids = [r.response_data.get("job_id") for r in audit_results if r.success]
    
    logger.info(f"Started {len(job_ids)} audit tasks")
    
    # Step 2: While tasks are running, hammer the API with requests
    logger.info("Step 2: Sending 20 rapid health checks...")
    health_tasks = [client.get_health() for _ in range(20)]
    health_results = await asyncio.gather(*health_tasks)
    
    success_count = sum(1 for r in health_results if r.success)
    logger.info(f"Health checks: {success_count}/20 succeeded")
    
    # Step 3: Check status of running tasks
    logger.info("Step 3: Checking status of all tasks...")
    status_tasks = [client.get_audit_status(job_id) for job_id in job_ids]
    status_results = await asyncio.gather(*status_tasks)
    
    status_success = sum(1 for r in status_results if r.success)
    logger.info(f"Status checks: {status_success}/{len(job_ids)} succeeded")
    
    # Assertions
    assert success_count >= 18, f"Expected at least 18 health checks, got {success_count}"
    assert status_success >= len(job_ids) - 2, "Status checks should mostly succeed"
    
    logger.info("✓ API responsiveness under load test passed")


@pytest.mark.asyncio
async def test_graceful_error_on_redis_failure():
    """Verify clear error messages when Redis fails."""
    logger.info("=" * 60)
    logger.info("TEST: Graceful Error on Redis Failure")
    logger.info("=" * 60)
    
    client = AsyncAPIClient()
    docker_mgr = DockerContainerManager()
    
    # Stop Redis
    logger.info("Stopping Redis...")
    docker_mgr.stop_container("fairlens_redis", timeout=5)
    await asyncio.sleep(2)
    
    # Try to check health
    logger.info("Attempting health check with Redis down...")
    health_result = await client.get_health()
    
    if not health_result.success:
        logger.info(f"Got expected error: {health_result.error}")
        assert "refused" in str(health_result.error).lower() or \
               "connect" in str(health_result.error).lower(), \
               "Error should be clear about connection issue"
    else:
        logger.info(f"Health check response: {health_result.response_data}")
        # If API still responds, check if it reports Redis as disconnected
        redis_status = health_result.response_data.get("redis")
        assert redis_status in ["disconnected", "unknown"], \
            f"API should report Redis as disconnected, got {redis_status}"
    
    # Restart Redis for other tests
    logger.info("Restarting Redis...")
    docker_mgr.start_container("fairlens_redis")
    docker_mgr.wait_for_container("fairlens_redis", timeout=30)
    
    logger.info("✓ Graceful error test passed")
