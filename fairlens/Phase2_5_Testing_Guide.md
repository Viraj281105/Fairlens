# Phase 2.5 Reliability Testing Suite

## Overview

Phase 2.5 transforms the system from **functionally correct** to **predictably reliable under load, failure, and recovery**.

This comprehensive testing suite validates:

1. ✅ **Concurrency & Load** - Can it handle 20+ concurrent requests?
2. ✅ **Worker Failure Recovery** - What happens when Celery worker crashes?
3. ✅ **Redis Outage Recovery** - Does it handle broker failures gracefully?
4. ✅ **Idempotency** - Are operations safe to retry?
5. ✅ **Latency Benchmarking** - What are the performance characteristics?
6. ✅ **Chaos Testing** - Does it survive random failures?
7. ✅ **Observability** - Can we see what's happening under stress?

---

## Architecture & System Under Test

```
┌──────────────────────────────────────────────────────────┐
│                     FastAPI Backend                      │
│          POST /upload, /audit/start, /audit/{id}        │
└────────────┬───────────────────────────────────────────┘
             │
        ┌────┴────┐
        ▼         ▼
    ┌─────────────────────────────────────────────────┐
    │         Redis (Broker + Result Backend)         │
    │         redis://localhost:6379/0                │
    └────────┬────────────────────────────────────┬──┘
             │                                    │
        ┌────▼─────────┐              ┌──────────▼────┐
        │ Celery Worker│              │     Flower    │
        │(task exec)   │              │(monitoring)   │
        └──────────────┘              └───────────────┘
```

---

## Prerequisites

### System Requirements
- Docker & Docker Compose (running)
- Python 3.11+
- pytest, pytest-asyncio, httpx

### Services Must Be Running
```bash
cd infra/
docker compose up -d
```

Verify all containers are healthy:
```bash
docker compose ps
```

Check API is responsive:
```bash
curl http://localhost:8000/health
```

---

## Test Suites

### 1. Load & Concurrency Testing (`test_load.py`)

Tests if the system handles concurrent traffic without degradation.

#### Tests Included:
- **test_concurrent_uploads_10** - 10 concurrent file uploads
- **test_concurrent_uploads_20** - 20 concurrent file uploads
- **test_concurrent_audits_after_uploads** - Multiple audits in parallel
- **test_no_hanging_requests** - Requests don't hang indefinitely (5s timeout)
- **test_task_not_stuck_in_pending** - Tasks move away from PENDING state
- **test_high_concurrency_stress** - 30 concurrent mixed operations
- **test_end_to_end_latency** - Upload → Audit completion time

#### Expected Results:
```
✓ All requests complete within reasonable time
✓ No requests hang beyond timeout
✓ Tasks transition from PENDING → PROGRESS → completion
✓ Success rate ≥ 90% under concurrent load
✓ P95 latency < 10 seconds
✓ Throughput ≥ 5 uploads/second
```

---

### 2. Failure Recovery Testing (`test_recovery.py`)

Tests system resilience when services fail.

#### Tests Included:
- **test_worker_crash_recovery** - Kill worker mid-task, restart, verify recovery
- **test_redis_outage_recovery** - Stop Redis, attempt operations, restart, verify recovery
- **test_api_remains_responsive_under_load** - Send requests while other services fail
- **test_graceful_error_on_redis_failure** - Verify clear error messages

#### Expected Results:
```
✓ Worker crash: Task is retried or fails with clear error (not lost)
✓ Worker restart: New tasks process successfully
✓ Redis outage: API returns clear error (graceful degradation)
✓ Redis restart: System recovers fully, new tasks work
✓ No silent failures or data corruption
✓ Error messages are clear and actionable
```

---

### 3. Idempotency Testing (`test_idempotency.py`)

Tests data safety with repeated operations.

#### Tests Included:
- **test_idempotency_same_file_sequential** - Upload same file 5 times in sequence
- **test_idempotency_same_file_parallel** - Upload same file 10 times in parallel
- **test_no_duplicate_side_effects** - Verify no duplicate processing
- **test_latency_p95_under_load** - P95 latency under 50 concurrent requests
- **test_latency_consistency** - Latency doesn't degrade over time
- **test_end_to_end_latency_percentiles** - Complete audit latency profile

#### Expected Results:
```
✓ Each upload creates unique dataset_id (no deduplication)
✓ Parallel uploads don't cause collisions
✓ Repeated operations on same data are safe
✓ P95 latency remains stable (< 3x degradation from P50)
✓ No memory leaks (latency consistent over multiple batches)
```

---

### 4. Chaos Testing (`test_chaos.py`)

Tests system behavior under random failures.

#### Tests Included:
- **test_chaos_random_worker_restart** - Randomly kill/restart worker for 30s
- **test_chaos_concurrent_with_redis_instability** - Requests while Redis restarts
- **test_chaos_system_does_not_corrupt** - Verify no unrecoverable state
- **test_chaos_errors_are_visible** - Errors are visible, not silent

#### Expected Results:
```
✓ System survives random restarts without data loss
✓ Some requests may fail during chaos, but system recovers
✓ No cascading failures or cascading restarts
✓ Error messages visible in logs (not silent failures)
✓ After chaos ends, system is fully operational
```

---

## Running Tests

### Run All Tests
**Linux/Mac:**
```bash
./run_phase2_5_tests.sh
```

**Windows (PowerShell):**
```powershell
.\run_phase2_5_tests.ps1
```

### Run Specific Test Suite
```bash
# Load testing only
./run_phase2_5_tests.sh load

# Or via pytest directly
cd tests/phase2_5
pytest test_load.py -v
```

### Run Single Test
```bash
cd tests/phase2_5
pytest test_load.py::test_concurrent_uploads_10 -v -s
```

### Run with Detailed Output
```bash
cd tests/phase2_5
pytest test_load.py -v -s --tb=short
```

---

## Test Utilities & Architecture

### AsyncAPIClient (`async_client.py`)
Async HTTP client for sending requests in parallel.

```python
from async_client import AsyncAPIClient

client = AsyncAPIClient(base_url="http://localhost:8000")

# Concurrent uploads
results = await client.concurrent_uploads(count=20)

# Get metrics
metrics = client.get_metrics()
print(f"Success rate: {metrics['success_rate_percent']:.1f}%")
print(f"P95 latency: {metrics['latency_ms']['p95']:.1f}ms")
```

### DockerContainerManager (`test_utils.py`)
Manages containers for failure simulation.

```python
from test_utils import DockerContainerManager

mgr = DockerContainerManager()
mgr.kill_container("fairlens_worker")
mgr.wait_for_container("fairlens_worker", timeout=30)
mgr.is_container_running("fairlens_redis")
```

### Enhanced Logging
All components log with structured format including task_id and job_id:

```
[TASK=abc123] [JOB=xyz789] TASK_STARTED: dataset_id=...
[TASK=abc123] [JOB=xyz789] LIFECYCLE: ingestion started
[TASK=abc123] [JOB=xyz789] LIFECYCLE: ingestion completed
[TASK=abc123] [JOB=xyz789] TASK_COMPLETED successfully in 45.23s
```

---

## Interpreting Results

### Success Criteria

| Metric | Threshold | What It Means |
|--------|-----------|---------------|
| Success Rate (Load) | ≥ 90% | Most requests succeed under concurrency |
| P95 Latency | < 10s | 95% of requests complete quickly |
| Worker Recovery | < 30s | System recovers from worker crash |
| Redis Recovery | < 30s | System recovers from broker outage |
| Chaos Survival | No data loss | System doesn't corrupt under random failures |

### Common Failure Modes

| Issue | Cause | Fix |
|-------|-------|-----|
| Tests fail to connect to API | Services not running | `docker compose up -d` |
| Worker keeps crashing | Task fails in pipeline | Check `docker logs fairlens_worker` |
| Redis health checks fail | Redis port blocked | Check firewall, restart Redis |
| Tasks stuck in PENDING | Worker not connected | Restart worker and Redis |
| Latency too high | Heavy tasks or resource contention | Check `docker stats` |

---

## Performance Benchmarks

### Expected Performance (on local Docker)

```
Upload latency:        50-200ms (P95 < 500ms)
API response time:     10-50ms for status checks
Task start to first progress:  < 2 seconds
End-to-end audit:      30-120 seconds (depends on data size)
Concurrent throughput: ≥ 5 uploads/second
P95 latency under 30 concurrent: < 10 seconds
Recovery time (worker crash): 5-30 seconds
Recovery time (Redis outage): 5-30 seconds
```

---

## Observability & Monitoring

### View Logs
```bash
# API logs
docker logs -f fairlens_api

# Worker logs
docker logs -f fairlens_worker

# Redis logs
docker logs -f fairlens_redis

# All logs with timestamps
docker logs -f --timestamps fairlens_worker
```

### Monitor Containers
```bash
# Real-time container stats
docker stats

# Check specific container
docker stats fairlens_worker --no-stream
```

### Check Task Status via Flower
```
http://localhost:5555
```

Visit Flower to see:
- Task history
- Worker status
- Task execution time
- Failure reasons

### Query Redis Directly
```bash
# Connect to Redis
docker exec -it fairlens_redis redis-cli

# Check task state
GET "celery-task-meta-<task_id>"
KEYS "celery-task-meta-*"
DBSIZE
```

---

## Troubleshooting

### Tests hang/timeout
1. Check if containers are running: `docker compose ps`
2. Check API health: `curl http://localhost:8000/health`
3. Increase timeout if tasks are slow: Edit `async_client.py` timeout parameter
4. Check logs: `docker logs fairlens_worker`

### Worker keeps crashing
1. Check logs: `docker logs fairlens_worker`
2. Look for import errors or dependency issues
3. Verify Redis is running and healthy
4. Restart worker: `docker restart fairlens_worker`

### Redis connection errors
1. Verify Redis is running: `docker ps | grep redis`
2. Check Redis logs: `docker logs fairlens_redis`
3. Verify port 6379 is accessible: `docker exec fairlens_redis redis-cli ping`
4. Restart Redis: `docker restart fairlens_redis`

### API not responding
1. Check if API container is running: `docker ps | grep api`
2. Check API logs: `docker logs fairlens_api`
3. Verify port 8000 is accessible: `curl http://localhost:8000/health`
4. Restart API: `docker restart fairlens_api`

---

## Next Steps: Addressing Issues

If tests reveal failures, follow this process:

### 1. Load Test Failures
**Problem:** High failure rate under concurrency
- Check worker CPU/memory: `docker stats`
- Increase worker threads in docker-compose: `--pool=threads --concurrency=10`
- Check for task timeouts in logs

### 2. Recovery Test Failures
**Problem:** System doesn't recover from crashes
- Verify retry configuration in Celery task
- Check if tasks are being retried (look in Flower)
- Ensure Redis persistence is configured

### 3. Chaos Test Failures
**Problem:** Data corruption or unrecoverable state
- Review transaction handling in pipeline
- Verify idempotent operations
- Check for partial failures without rollback

### 4. Latency Issues
**Problem:** P95 latency exceeds threshold
- Profile the task: Add timing logs to each pipeline stage
- Check for bottlenecks in ingestion/processing
- Consider async pipeline stages

---

## Advanced: Custom Test Scenarios

### Add New Load Test
```python
# tests/phase2_5/test_load.py
@pytest.mark.asyncio
async def test_my_custom_load():
    client = AsyncAPIClient()
    results = await client.concurrent_uploads(count=50)
    metrics = client.get_metrics()
    # Your assertions here
```

### Add New Failure Scenario
```python
# tests/phase2_5/test_recovery.py
@pytest.mark.asyncio
async def test_my_custom_failure():
    docker_mgr = DockerContainerManager()
    # Your failure simulation
    # Your assertions
```

---

## Production Readiness Checklist

After passing Phase 2.5 tests:

- [ ] All load tests pass (≥ 90% success rate)
- [ ] All recovery tests pass (system survives failures)
- [ ] All chaos tests pass (no data corruption)
- [ ] Latency meets SLA (P95 < 10s)
- [ ] Error messages are clear and actionable
- [ ] Logs include tracing IDs for debugging
- [ ] Flower monitoring is working
- [ ] Docker resource limits are appropriate
- [ ] Retry logic is configured
- [ ] Alert thresholds are set

---

## Support & Debugging

For detailed test output and debugging:

```bash
# Run with full traceback
pytest test_load.py -v --tb=long

# Run with print statements
pytest test_load.py -v -s

# Run in parallel (faster, but harder to debug)
pytest test_load.py -v -n auto

# Generate HTML report
pytest test_load.py --html=report.html
```

---

## References

- [Celery Documentation](https://docs.celeryproject.org/)
- [Flower Monitoring](https://flower.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-events/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
