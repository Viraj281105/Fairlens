"""Phase 2.5 - Chaos Testing (Lite)"""
import pytest
import asyncio
import time
import logging
import random
from test_utils import DockerContainerManager
from async_client import AsyncAPIClient

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_chaos_random_worker_restart():
    """Randomly kill and restart worker while sending requests."""
    logger.info("=" * 60)
    logger.info("TEST: Chaos - Random Worker Restart")
    logger.info("=" * 60)
    
    client = AsyncAPIClient()
    docker_mgr = DockerContainerManager()
    
    logger.info("Starting chaos test: Random worker restarts for 30 seconds")
    
    start = time.time()
    chaos_duration = 30  # seconds
    
    async def send_requests():
        """Continuously send requests."""
        results = []
        while time.time() - start < chaos_duration:
            result = await client.create_dataset()
            results.append(result)
            await asyncio.sleep(random.uniform(0.5, 2))
        return results
    
    async def chaos_worker_kills():
        """Randomly kill and restart worker."""
        while time.time() - start < chaos_duration:
            await asyncio.sleep(random.uniform(5, 15))
            
            logger.info("CHAOS: Killing worker...")
            docker_mgr.kill_container("fairlens_worker")
            await asyncio.sleep(2)
            
            logger.info("CHAOS: Restarting worker...")
            docker_mgr.restart_container("fairlens_worker")
            docker_mgr.wait_for_container("fairlens_worker", timeout=20)
    
    # Run both concurrently
    request_results, _ = await asyncio.gather(
        send_requests(),
        chaos_worker_kills(),
        return_exceptions=True
    )
    
    # Count successes
    success_count = sum(1 for r in request_results if isinstance(r, object) and hasattr(r, 'success') and r.success)
    total = len([r for r in request_results if isinstance(r, object)])
    
    logger.info(f"Chaos test complete: {success_count}/{total} requests succeeded")
    
    # System should handle chaos gracefully (some failures OK, but not all)
    assert success_count > 0, "At least some requests should succeed even during chaos"
    
    logger.info("✓ Chaos worker restart test passed")


@pytest.mark.asyncio
async def test_chaos_concurrent_with_redis_instability():
    """Send requests while Redis is repeatedly restarted."""
    logger.info("=" * 60)
    logger.info("TEST: Chaos - Concurrent Requests with Redis Instability")
    logger.info("=" * 60)
    
    client = AsyncAPIClient()
    docker_mgr = DockerContainerManager()
    
    logger.info("Starting chaos test: Requests with Redis restarts for 20 seconds")
    
    start = time.time()
    chaos_duration = 20
    
    async def send_requests():
        """Continuously send requests."""
        results = []
        while time.time() - start < chaos_duration:
            result = await client.get_health()
            results.append(result)
            await asyncio.sleep(random.uniform(0.2, 1))
        return results
    
    async def chaos_redis_restarts():
        """Restart Redis multiple times."""
        await asyncio.sleep(3)  # Let some requests go through first
        
        for cycle in range(2):
            logger.info(f"CHAOS: Stopping Redis (cycle {cycle+1})...")
            docker_mgr.stop_container("fairlens_redis", timeout=3)
            await asyncio.sleep(2)
            
            logger.info(f"CHAOS: Starting Redis (cycle {cycle+1})...")
            docker_mgr.start_container("fairlens_redis")
            docker_mgr.wait_for_container("fairlens_redis", timeout=20)
            await asyncio.sleep(2)
    
    # Run both concurrently
    request_results, _ = await asyncio.gather(
        send_requests(),
        chaos_redis_restarts(),
        return_exceptions=True
    )
    
    # Verify we got a mix of responses
    total_results = len([r for r in request_results if isinstance(r, object)])
    successful = sum(1 for r in request_results if isinstance(r, object) and hasattr(r, 'success') and r.success)
    
    logger.info(f"Chaos test complete: {successful}/{total_results} health checks succeeded")
    
    # Should have some successes both with and without Redis
    assert total_results > 0, "Should have recorded results"
    assert successful > total_results // 4, "Should have reasonable success rate"
    
    logger.info("✓ Chaos Redis instability test passed")


@pytest.mark.asyncio
async def test_chaos_system_does_not_corrupt():
    """Verify system doesn't enter unrecoverable state during chaos."""
    logger.info("=" * 60)
    logger.info("TEST: Chaos - No Unrecoverable State")
    logger.info("=" * 60)
    
    client = AsyncAPIClient()
    docker_mgr = DockerContainerManager()
    
    logger.info("Starting chaos: Random container restarts")
    
    # Run chaos for a bit
    for i in range(3):
        container = random.choice(["fairlens_worker", "fairlens_redis", "fairlens_api"])
        logger.info(f"Chaos cycle {i+1}: Restarting {container}...")
        
        docker_mgr.restart_container(container)
        docker_mgr.wait_for_container(container, timeout=30)
        await asyncio.sleep(3)
    
    # After chaos, verify system is still operational
    logger.info("Verifying system after chaos...")
    
    health = await client.get_health()
    assert health.success, "API should still be reachable after chaos"
    
    upload = await client.create_dataset()
    assert upload.success, "Upload should work after chaos"
    
    if upload.success:
        dataset_id = upload.response_data.get("dataset_id")
        audit = await client.start_audit(dataset_id)
        assert audit.success, "Audit should start after chaos"
    
    logger.info("✓ System recovered from chaos successfully")


@pytest.mark.asyncio
async def test_chaos_errors_are_visible():
    """Verify errors during chaos are visible and not silent."""
    logger.info("=" * 60)
    logger.info("TEST: Chaos - Errors Are Visible")
    logger.info("=" * 60)
    
    client = AsyncAPIClient()
    docker_mgr = DockerContainerManager()
    
    logger.info("Killing Redis and checking for visible errors...")
    
    # Kill Redis
    docker_mgr.kill_container("fairlens_redis")
    await asyncio.sleep(2)
    
    # Try various operations
    logger.info("Checking health with Redis down...")
    health_result = await client.get_health()
    
    # Should either fail with clear error or report degraded status
    if not health_result.success:
        assert health_result.error is not None, "Failed request should have error message"
        logger.info(f"Got expected error: {health_result.error}")
    else:
        # Or report degraded status
        redis_status = health_result.response_data.get("redis", "unknown")
        logger.info(f"API health: {health_result.response_data.get('status')}, Redis: {redis_status}")
        assert redis_status in ["disconnected", "unknown", "error"], "Should indicate Redis issue"
    
    # Restart Redis for other tests
    logger.info("Restarting Redis...")
    docker_mgr.start_container("fairlens_redis")
    docker_mgr.wait_for_container("fairlens_redis", timeout=30)
    
    logger.info("✓ Error visibility test passed")
