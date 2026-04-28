"""Phase 2.5 - Load and Concurrency Testing"""
import pytest
import asyncio
import logging
import time
from typing import List, Dict, Any
from async_client import AsyncAPIClient, RequestResult

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_concurrent_uploads_10():
    """Test 10 concurrent file uploads."""
    logger.info("=" * 60)
    logger.info("TEST: Concurrent Uploads (10)")
    logger.info("=" * 60)
    
    client = AsyncAPIClient()
    results = await client.concurrent_uploads(count=10)
    
    assert len(results) == 10
    success_count = sum(1 for r in results if r["upload"]["success"])
    
    logger.info(f"Successful uploads: {success_count}/10")
    logger.info(f"Success rate: {success_count/10*100:.1f}%")
    
    # Log latencies
    latencies = [r["upload"]["latency_ms"] for r in results if r["upload"]["success"]]
    if latencies:
        logger.info(f"Latency - Min: {min(latencies):.1f}ms, Max: {max(latencies):.1f}ms, Avg: {sum(latencies)/len(latencies):.1f}ms")
    
    assert success_count >= 9, f"Expected at least 9 successful uploads, got {success_count}"


@pytest.mark.asyncio
async def test_concurrent_uploads_20():
    """Test 20 concurrent file uploads."""
    logger.info("=" * 60)
    logger.info("TEST: Concurrent Uploads (20)")
    logger.info("=" * 60)
    
    client = AsyncAPIClient()
    results = await client.concurrent_uploads(count=20)
    
    assert len(results) == 20
    success_count = sum(1 for r in results if r["upload"]["success"])
    
    logger.info(f"Successful uploads: {success_count}/20")
    logger.info(f"Success rate: {success_count/20*100:.1f}%")
    
    latencies = [r["upload"]["latency_ms"] for r in results if r["upload"]["success"]]
    if latencies:
        logger.info(f"Latency - Min: {min(latencies):.1f}ms, Max: {max(latencies):.1f}ms, Avg: {sum(latencies)/len(latencies):.1f}ms")
    
    assert success_count >= 18, f"Expected at least 18 successful uploads, got {success_count}"


@pytest.mark.asyncio
async def test_concurrent_audits_after_uploads():
    """Test concurrent audit start requests after uploads."""
    logger.info("=" * 60)
    logger.info("TEST: Concurrent Audits After Uploads")
    logger.info("=" * 60)
    
    client = AsyncAPIClient()
    
    # First, upload 15 datasets
    upload_results = await client.concurrent_uploads(count=15)
    dataset_ids = [
        r["upload"]["dataset_id"] 
        for r in upload_results 
        if r["upload"]["success"] and r["upload"]["dataset_id"]
    ]
    
    logger.info(f"Created {len(dataset_ids)} datasets, starting audits...")
    
    # Start audits concurrently
    audit_results = await client.concurrent_audits(dataset_ids)
    
    success_count = sum(1 for r in audit_results if r.success)
    logger.info(f"Successful audit starts: {success_count}/{len(dataset_ids)}")
    
    assert success_count >= len(dataset_ids) - 2, "Most audits should start successfully"


@pytest.mark.asyncio
async def test_no_hanging_requests():
    """Verify no requests hang indefinitely (timeout test)."""
    logger.info("=" * 60)
    logger.info("TEST: No Hanging Requests (5 sec timeout)")
    logger.info("=" * 60)
    
    client = AsyncAPIClient(timeout=5.0)  # Short timeout to catch hangs
    
    tasks = [client.create_dataset() for _ in range(5)]
    results = await asyncio.gather(*tasks)
    
    # All should complete within 5 seconds (per result.latency_ms)
    hanging = [r for r in results if r.latency_ms > 5000]
    
    logger.info(f"Completed {len(results)} requests without hanging")
    logger.info(f"Requests exceeding 5s: {len(hanging)}")
    
    assert len(hanging) == 0, "No requests should hang"


@pytest.mark.asyncio
async def test_task_not_stuck_in_pending():
    """Verify tasks don't get stuck in PENDING state."""
    logger.info("=" * 60)
    logger.info("TEST: No Stuck Tasks (PENDING state)")
    logger.info("=" * 60)
    
    client = AsyncAPIClient()
    
    # Upload and start audit
    upload_result, audit_result = await client.upload_and_audit()
    assert upload_result.success and audit_result.success
    
    job_id = audit_result.response_data.get("job_id")
    logger.info(f"Started audit job: {job_id}")
    
    # Wait for task to move away from PENDING
    max_wait = 15  # seconds
    start = time.time()
    
    while time.time() - start < max_wait:
        status_result = await client.get_audit_status(job_id)
        if status_result.success:
            task_status = status_result.response_data.get("task_status")
            logger.info(f"Task status: {task_status}")
            
            assert task_status != "PENDING", f"Task should not stay in PENDING, got {task_status}"
            break
        
        await asyncio.sleep(1)
    else:
        pytest.fail(f"Task still PENDING after {max_wait} seconds")


@pytest.mark.asyncio
async def test_high_concurrency_stress():
    """Stress test with 30 concurrent operations (mix of uploads and status checks)."""
    logger.info("=" * 60)
    logger.info("TEST: High Concurrency Stress (30 concurrent)")
    logger.info("=" * 60)
    
    client = AsyncAPIClient()
    
    # Start 30 concurrent uploads
    start = time.time()
    results = await client.concurrent_uploads(count=30)
    elapsed = time.time() - start
    
    success_count = sum(1 for r in results if r["upload"]["success"])
    
    logger.info(f"Completed 30 concurrent uploads in {elapsed:.2f}s")
    logger.info(f"Success rate: {success_count}/30 ({success_count/30*100:.1f}%)")
    logger.info(f"Throughput: {30/elapsed:.1f} uploads/sec")
    
    metrics = client.get_metrics()
    logger.info(f"Latency stats:")
    logger.info(f"  Min: {metrics['latency_ms']['min']:.1f}ms")
    logger.info(f"  Avg: {metrics['latency_ms']['avg']:.1f}ms")
    logger.info(f"  Max: {metrics['latency_ms']['max']:.1f}ms")
    logger.info(f"  P95: {metrics['latency_ms']['p95']:.1f}ms")
    
    assert success_count >= 27, f"Expected at least 27 successful uploads, got {success_count}"


@pytest.mark.asyncio
async def test_end_to_end_latency():
    """Measure end-to-end latency from upload to task completion."""
    logger.info("=" * 60)
    logger.info("TEST: End-to-End Latency (with task completion)")
    logger.info("=" * 60)
    
    client = AsyncAPIClient()
    
    # Upload dataset
    upload_result = await client.create_dataset()
    assert upload_result.success
    
    dataset_id = upload_result.response_data.get("dataset_id")
    upload_time = upload_result.latency_ms
    
    logger.info(f"Upload completed in {upload_time:.1f}ms")
    
    # Start audit
    audit_result = await client.start_audit(dataset_id)
    assert audit_result.success
    
    job_id = audit_result.response_data.get("job_id")
    start_time = time.time()
    
    # Poll until completion (max 2 minutes)
    final_status = await client.poll_status_until_complete(job_id, max_wait_sec=120)
    
    total_time = (time.time() - start_time) * 1000
    
    if final_status:
        task_status = final_status.get("task_status")
        logger.info(f"Task completed with status: {task_status}")
        logger.info(f"Total audit time: {total_time/1000:.2f}s ({total_time:.0f}ms)")
    else:
        logger.warning(f"Task did not complete within 120 seconds")
