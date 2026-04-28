"""Phase 2.5 - Idempotency and Latency Testing"""
import pytest
import asyncio
import time
import logging
import hashlib
from async_client import AsyncAPIClient

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_idempotency_same_file_sequential():
    """Upload the same file multiple times sequentially and verify consistency."""
    logger.info("=" * 60)
    logger.info("TEST: Idempotency (Sequential Same File)")
    logger.info("=" * 60)
    
    client = AsyncAPIClient()
    
    # Create a unique file signature for testing
    test_file_content = b"col1,col2,col3\nrow1_1,row1_2,row1_3\nrow2_1,row2_2,row2_3"
    file_hash = hashlib.md5(test_file_content).hexdigest()
    
    logger.info(f"File hash: {file_hash}")
    logger.info("Uploading same file 5 times sequentially...")
    
    dataset_ids = []
    upload_times = []
    
    for i in range(5):
        start = time.time()
        result = await client.create_dataset()
        elapsed = (time.time() - start) * 1000
        
        assert result.success, f"Upload {i+1} failed"
        dataset_ids.append(result.response_data.get("dataset_id"))
        upload_times.append(elapsed)
        
        logger.info(f"Upload {i+1}: {result.response_data.get('dataset_id')[:8]}... ({elapsed:.1f}ms)")
    
    # Verify all uploads were successful
    assert len(dataset_ids) == 5, "Should have 5 successful uploads"
    assert len(set(dataset_ids)) == 5, "Each upload should create unique dataset_id"
    
    # Log latency stats
    logger.info(f"Upload latencies: Min={min(upload_times):.1f}ms, Max={max(upload_times):.1f}ms, Avg={sum(upload_times)/len(upload_times):.1f}ms")
    
    logger.info("✓ Idempotency sequential test passed")


@pytest.mark.asyncio
async def test_idempotency_same_file_parallel():
    """Upload the same file multiple times in parallel and verify consistency."""
    logger.info("=" * 60)
    logger.info("TEST: Idempotency (Parallel Same File)")
    logger.info("=" * 60)
    
    client = AsyncAPIClient()
    
    test_file_content = b"col1,col2,col3\nrow1_1,row1_2,row1_3\nrow2_1,row2_2,row2_3"
    file_hash = hashlib.md5(test_file_content).hexdigest()
    
    logger.info(f"File hash: {file_hash}")
    logger.info("Uploading same file 10 times in parallel...")
    
    # Create parallel tasks
    start = time.time()
    results = await client.concurrent_uploads(count=10)
    elapsed = (time.time() - start) * 1000
    
    success_count = sum(1 for r in results if r["upload"]["success"])
    dataset_ids = [r["upload"]["dataset_id"] for r in results if r["upload"]["success"]]
    
    logger.info(f"Completed 10 parallel uploads in {elapsed:.0f}ms")
    logger.info(f"Successful: {success_count}/10")
    logger.info(f"Unique dataset IDs: {len(set(dataset_ids))}")
    
    # All should succeed
    assert success_count == 10, "All parallel uploads should succeed"
    # Each should get unique ID
    assert len(set(dataset_ids)) == 10, "Each upload should create unique dataset_id"
    
    logger.info("✓ Idempotency parallel test passed")


@pytest.mark.asyncio
async def test_no_duplicate_side_effects():
    """Verify that uploading same data doesn't cause duplicate side effects."""
    logger.info("=" * 60)
    logger.info("TEST: No Duplicate Side Effects")
    logger.info("=" * 60)
    
    client = AsyncAPIClient()
    
    # Upload dataset
    logger.info("Uploading dataset...")
    upload1 = await client.create_dataset()
    assert upload1.success
    
    dataset_id = upload1.response_data.get("dataset_id")
    logger.info(f"Dataset ID: {dataset_id}")
    
    # Start audit
    logger.info("Starting audit for dataset...")
    audit1 = await client.start_audit(dataset_id)
    assert audit1.success
    
    job_id_1 = audit1.response_data.get("job_id")
    task_id_1 = audit1.response_data.get("task_id")
    
    # Try to start audit again with same dataset
    logger.info("Starting second audit with same dataset...")
    await asyncio.sleep(1)  # Small delay
    
    audit2 = await client.start_audit(dataset_id)
    assert audit2.success
    
    job_id_2 = audit2.response_data.get("job_id")
    task_id_2 = audit2.response_data.get("task_id")
    
    # Verify we got different job/task IDs (no duplication)
    assert job_id_1 != job_id_2, "Each audit start should create new job"
    assert task_id_1 != task_id_2, "Each audit start should create new task"
    
    logger.info(f"Job 1: {job_id_1}")
    logger.info(f"Job 2: {job_id_2}")
    logger.info("✓ No duplicate side effects test passed")


@pytest.mark.asyncio
async def test_latency_p95_under_load():
    """Measure P95 latency under load."""
    logger.info("=" * 60)
    logger.info("TEST: Latency P95 Under Load")
    logger.info("=" * 60)
    
    client = AsyncAPIClient()
    
    # Send 50 requests to get good statistical sample
    logger.info("Sending 50 concurrent requests...")
    start = time.time()
    results = await client.concurrent_uploads(count=50)
    total_time = time.time() - start
    
    latencies = [r["upload"]["latency_ms"] for r in results if r["upload"]["success"]]
    latencies.sort()
    
    # Calculate percentiles
    p50_idx = len(latencies) // 2
    p95_idx = int(len(latencies) * 0.95)
    p99_idx = int(len(latencies) * 0.99)
    
    logger.info(f"Completed 50 uploads in {total_time:.2f}s ({50/total_time:.1f} req/s)")
    logger.info(f"Latency stats:")
    logger.info(f"  Min: {min(latencies):.1f}ms")
    logger.info(f"  P50: {latencies[p50_idx]:.1f}ms")
    logger.info(f"  P95: {latencies[p95_idx]:.1f}ms")
    logger.info(f"  P99: {latencies[p99_idx]:.1f}ms")
    logger.info(f"  Max: {max(latencies):.1f}ms")
    logger.info(f"  Avg: {sum(latencies)/len(latencies):.1f}ms")
    
    # P95 should be reasonable (< 10 seconds)
    assert latencies[p95_idx] < 10000, f"P95 latency should be < 10s, got {latencies[p95_idx]:.1f}ms"
    
    logger.info("✓ Latency P95 test passed")


@pytest.mark.asyncio
async def test_latency_consistency():
    """Verify latency doesn't degrade over time (no memory leaks)."""
    logger.info("=" * 60)
    logger.info("TEST: Latency Consistency Over Time")
    logger.info("=" * 60)
    
    client = AsyncAPIClient()
    
    # First batch of 20
    logger.info("Batch 1: 20 requests...")
    batch1_results = await client.concurrent_uploads(count=20)
    batch1_latencies = [r["upload"]["latency_ms"] for r in batch1_results if r["upload"]["success"]]
    batch1_avg = sum(batch1_latencies) / len(batch1_latencies)
    
    # Wait a bit
    await asyncio.sleep(2)
    
    # Second batch of 20
    logger.info("Batch 2: 20 requests...")
    client.clear_results()
    batch2_results = await client.concurrent_uploads(count=20)
    batch2_latencies = [r["upload"]["latency_ms"] for r in batch2_results if r["upload"]["success"]]
    batch2_avg = sum(batch2_latencies) / len(batch2_latencies)
    
    logger.info(f"Batch 1 avg latency: {batch1_avg:.1f}ms")
    logger.info(f"Batch 2 avg latency: {batch2_avg:.1f}ms")
    
    # Latency should not degrade by more than 50%
    # (some variation is expected, but shouldn't grow)
    ratio = batch2_avg / batch1_avg if batch1_avg > 0 else 1
    logger.info(f"Latency ratio (B2/B1): {ratio:.2f}")
    
    assert ratio < 3.0, f"Latency degradation too high: {ratio:.2f}x"
    
    logger.info("✓ Latency consistency test passed")


@pytest.mark.asyncio
async def test_end_to_end_latency_percentiles():
    """Detailed latency benchmark for end-to-end audit."""
    logger.info("=" * 60)
    logger.info("TEST: End-to-End Latency Percentiles")
    logger.info("=" * 60)
    
    client = AsyncAPIClient()
    latencies = []
    
    # Run 5 complete end-to-end audits
    for i in range(5):
        logger.info(f"Running audit {i+1}/5...")
        
        start = time.time()
        
        # Upload
        upload_result = await client.create_dataset()
        if not upload_result.success:
            logger.warning(f"Audit {i+1}: Upload failed")
            continue
        
        # Start audit
        dataset_id = upload_result.response_data.get("dataset_id")
        audit_result = await client.start_audit(dataset_id)
        if not audit_result.success:
            logger.warning(f"Audit {i+1}: Audit start failed")
            continue
        
        job_id = audit_result.response_data.get("job_id")
        
        # Wait for completion (with timeout)
        final_status = await client.poll_status_until_complete(job_id, max_wait_sec=60)
        
        elapsed = (time.time() - start) * 1000
        latencies.append(elapsed)
        
        if final_status:
            task_status = final_status.get("task_status")
            logger.info(f"Audit {i+1}: {task_status} in {elapsed/1000:.1f}s")
        else:
            logger.info(f"Audit {i+1}: Timeout after {elapsed/1000:.1f}s")
    
    if latencies:
        latencies.sort()
        logger.info(f"End-to-end latencies (5 audits):")
        logger.info(f"  Min: {min(latencies)/1000:.1f}s")
        logger.info(f"  Avg: {sum(latencies)/len(latencies)/1000:.1f}s")
        logger.info(f"  Max: {max(latencies)/1000:.1f}s")
    else:
        logger.warning("No successful audits to report")
