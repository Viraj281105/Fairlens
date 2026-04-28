# Quick Reference: Phase 2.5 Testing

## One-Minute Start Guide

### 1. Start the System
```bash
cd infra/
docker compose up -d
```

### 2. Run All Tests
**Windows (PowerShell):**
```powershell
.\run_phase2_5_tests.ps1
```

**Linux/Mac (Bash):**
```bash
chmod +x run_phase2_5_tests.sh
./run_phase2_5_tests.sh
```

### 3. Check Results
- ✅ Green = PASSED
- ❌ Red = FAILED
- ⏱️ Check latency metrics in output

---

## What Each Test Suite Does

| Suite | What It Tests | Run Time |
|-------|---------------|----------|
| Load | 10-30 concurrent requests | ~30s |
| Idempotency | Same data uploaded multiple times | ~60s |
| Recovery | System survives crashes | ~120s |
| Chaos | Random failures don't break system | ~90s |

**Total: ~5 minutes**

---

## Quick Commands

### Run Specific Suite
```bash
cd tests/phase2_5
pytest test_load.py -v
```

### Run Single Test
```bash
pytest test_load.py::test_concurrent_uploads_10 -v -s
```

### View System Logs
```bash
docker logs -f fairlens_worker
docker logs -f fairlens_api
```

### Monitor Task Status
```
http://localhost:5555  (Flower)
http://localhost:8000/health  (API health)
```

### Check Container Health
```bash
docker compose ps
docker stats
```

---

## Success Indicators

✅ **All tests pass**: System is production-ready for reliability
✅ **Success rate ≥ 90%**: Can handle concurrent load
✅ **No data loss**: Survives crashes and failures
✅ **P95 < 10s**: Latency acceptable under load
✅ **Errors are visible**: No silent failures

---

## If Tests Fail

### 1. Check Services
```bash
docker compose ps
```
All should show "Up"

### 2. Check Logs
```bash
docker logs fairlens_worker
docker logs fairlens_api
```

### 3. Check Health
```bash
curl http://localhost:8000/health
```

### 4. Restart Everything
```bash
docker compose down
docker compose up -d
```

### 5. Run Tests Again
```bash
./run_phase2_5_tests.sh
```

---

## Expected Output Example

```
╔════════════════════════════════════════════════════════════╗
║ Phase 2.5 Reliability Testing Suite                        ║
║ Starting Phase 2.5 Tests                                   ║
╚════════════════════════════════════════════════════════════╝

━━━ Checking Docker ━━━
✓ Docker found
✓ Docker daemon is running

━━━ Checking Containers ━━━
✓ fairlens_api is running
✓ fairlens_worker is running
✓ fairlens_redis is running

━━━ Checking API Health ━━━
✓ API is responsive

━━━ Running: Load & Concurrency Testing ━━━
test_load.py::test_concurrent_uploads_10 PASSED                [20%]
test_load.py::test_concurrent_uploads_20 PASSED                [40%]
...
✓ Load & Concurrency Testing passed

━━━ Running: Idempotency Testing ━━━
test_idempotency.py::test_idempotency_same_file_sequential PASSED [20%]
...
✓ Idempotency Testing passed

━━━ Running: Failure Recovery Testing ━━━
test_recovery.py::test_worker_crash_recovery PASSED           [25%]
...
✓ Failure Recovery Testing passed

━━━ Running: Chaos Testing ━━━
test_chaos.py::test_chaos_random_worker_restart PASSED        [25%]
...
✓ Chaos Testing passed

╔════════════════════════════════════════════════════════════╗
║ Test Execution Complete                                    ║
╚════════════════════════════════════════════════════════════╝

✓ All test suites passed!

✓ System is production-ready for reliability.
```

---

## Performance Expectations

### Uploads
- Single: 50-200ms
- 10 concurrent: ≤ 2 seconds
- 20 concurrent: ≤ 5 seconds

### Audits
- Start: ≤ 100ms
- Status check: ≤ 50ms
- Full completion: 30-120s

### Under Chaos
- Worker crash recovery: < 30s
- Redis outage recovery: < 30s
- No data loss

---

## Files Generated

```
tests/phase2_5/
├── __init__.py              # Package init
├── conftest.py              # Pytest configuration
├── test_utils.py            # Docker & Redis utilities
├── async_client.py          # Async HTTP client
├── test_load.py             # Load tests
├── test_recovery.py         # Recovery tests
├── test_idempotency.py      # Idempotency tests
└── test_chaos.py            # Chaos tests
```

---

## Troubleshooting Matrix

| Symptom | Cause | Solution |
|---------|-------|----------|
| Tests won't start | Services not running | `docker compose up -d` |
| Lots of failures | Worker crashing | Check: `docker logs fairlens_worker` |
| High latency | Resource contention | Check: `docker stats` |
| Redis errors | Redis port blocked | Restart: `docker restart fairlens_redis` |
| API errors | API down | Restart: `docker restart fairlens_api` |
| Timeout errors | Tasks too slow | Increase timeout in `async_client.py` |

---

## Next Level: Custom Tests

Add your own tests to `tests/phase2_5/`:

```python
# test_custom.py
import pytest
from async_client import AsyncAPIClient

@pytest.mark.asyncio
async def test_my_scenario():
    client = AsyncAPIClient()
    result = await client.create_dataset()
    assert result.success
```

Then run:
```bash
pytest test_custom.py -v
```

---

## Support

- Check logs: `docker logs <container>`
- View metrics: Flower at `http://localhost:5555`
- Monitor live: `docker stats`
- Debug single test: `pytest -v -s test_file.py::test_name`

---

**Phase 2.5 Complete**: Your system is now production-ready for reliability! 🚀
