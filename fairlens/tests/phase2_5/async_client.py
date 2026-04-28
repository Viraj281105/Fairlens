"""Async HTTP client utilities for testing."""
import httpx
import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class RequestResult:
    """Result of a single HTTP request."""
    success: bool
    status_code: Optional[int]
    response_data: Optional[Dict[str, Any]]
    error: Optional[str]
    latency_ms: float
    timestamp: float


class AsyncAPIClient:
    """Async HTTP client for load testing."""
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0):
        self.base_url = base_url
        self.timeout = timeout
        self.results: List[RequestResult] = []

    async def get_health(self) -> RequestResult:
        """Check API health."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            start = time.time()
            try:
                response = await client.get(f"{self.base_url}/health")
                latency = (time.time() - start) * 1000
                return RequestResult(
                    success=response.status_code == 200,
                    status_code=response.status_code,
                    response_data=response.json(),
                    error=None,
                    latency_ms=latency,
                    timestamp=start
                )
            except Exception as e:
                latency = (time.time() - start) * 1000
                return RequestResult(
                    success=False,
                    status_code=None,
                    response_data=None,
                    error=str(e),
                    latency_ms=latency,
                    timestamp=start
                )

    async def create_dataset(self) -> RequestResult:
        """Simulate dataset upload."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            start = time.time()
            try:
                # Create dummy file content
                files = {"file": ("test_dataset.csv", b"col1,col2,col3\n1,2,3\n4,5,6")}
                response = await client.post(f"{self.base_url}/upload", files=files)
                latency = (time.time() - start) * 1000
                return RequestResult(
                    success=response.status_code == 200,
                    status_code=response.status_code,
                    response_data=response.json(),
                    error=None,
                    latency_ms=latency,
                    timestamp=start
                )
            except Exception as e:
                latency = (time.time() - start) * 1000
                return RequestResult(
                    success=False,
                    status_code=None,
                    response_data=None,
                    error=str(e),
                    latency_ms=latency,
                    timestamp=start
                )

    async def start_audit(self, dataset_id: str) -> RequestResult:
        """Start an audit task."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            start = time.time()
            try:
                payload = {"dataset_id": dataset_id}
                response = await client.post(
                    f"{self.base_url}/audit/start",
                    json=payload
                )
                latency = (time.time() - start) * 1000
                return RequestResult(
                    success=response.status_code == 200,
                    status_code=response.status_code,
                    response_data=response.json(),
                    error=None,
                    latency_ms=latency,
                    timestamp=start
                )
            except Exception as e:
                latency = (time.time() - start) * 1000
                return RequestResult(
                    success=False,
                    status_code=None,
                    response_data=None,
                    error=str(e),
                    latency_ms=latency,
                    timestamp=start
                )

    async def get_audit_status(self, job_id: str) -> RequestResult:
        """Get audit task status."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            start = time.time()
            try:
                response = await client.get(f"{self.base_url}/audit/{job_id}")
                latency = (time.time() - start) * 1000
                return RequestResult(
                    success=response.status_code == 200,
                    status_code=response.status_code,
                    response_data=response.json(),
                    error=None,
                    latency_ms=latency,
                    timestamp=start
                )
            except Exception as e:
                latency = (time.time() - start) * 1000
                return RequestResult(
                    success=False,
                    status_code=None,
                    response_data=None,
                    error=str(e),
                    latency_ms=latency,
                    timestamp=start
                )

    async def upload_and_audit(self) -> tuple[RequestResult, Optional[RequestResult]]:
        """Upload dataset and start audit (combined operation)."""
        upload_result = await self.create_dataset()
        if not upload_result.success:
            return upload_result, None
        
        dataset_id = upload_result.response_data.get("dataset_id")
        audit_result = await self.start_audit(dataset_id)
        return upload_result, audit_result

    async def concurrent_uploads(self, count: int) -> List[Dict[str, Any]]:
        """Send multiple concurrent uploads."""
        tasks = [self.create_dataset() for _ in range(count)]
        results = await asyncio.gather(*tasks)
        self.results.extend(results)
        
        return [
            {
                "upload": {
                    "success": r.success,
                    "status_code": r.status_code,
                    "latency_ms": r.latency_ms,
                    "dataset_id": r.response_data.get("dataset_id") if r.success else None
                }
            }
            for r in results
        ]

    async def concurrent_audits(self, dataset_ids: List[str]) -> List[RequestResult]:
        """Start audits for multiple datasets concurrently."""
        tasks = [self.start_audit(dataset_id) for dataset_id in dataset_ids]
        results = await asyncio.gather(*tasks)
        self.results.extend(results)
        return results

    async def poll_status_until_complete(
        self,
        job_id: str,
        max_wait_sec: float = 120,
        poll_interval_sec: float = 1.0
    ) -> Optional[Dict[str, Any]]:
        """Poll task status until completion or timeout."""
        start = time.time()
        while time.time() - start < max_wait_sec:
            result = await self.get_audit_status(job_id)
            if not result.success:
                logger.warning(f"Failed to get status for {job_id}: {result.error}")
                await asyncio.sleep(poll_interval_sec)
                continue
            
            status = result.response_data.get("task_status")
            if status in ["SUCCESS", "FAILURE"]:
                return result.response_data
            
            await asyncio.sleep(poll_interval_sec)
        
        return None

    def get_metrics(self) -> Dict[str, Any]:
        """Calculate metrics from all recorded results."""
        if not self.results:
            return {"error": "No results recorded"}
        
        success_count = sum(1 for r in self.results if r.success)
        failed_count = len(self.results) - success_count
        latencies = [r.latency_ms for r in self.results if r.success]
        
        return {
            "total_requests": len(self.results),
            "successful_requests": success_count,
            "failed_requests": failed_count,
            "success_rate_percent": (success_count / len(self.results) * 100) if self.results else 0,
            "latency_ms": {
                "min": min(latencies) if latencies else 0,
                "max": max(latencies) if latencies else 0,
                "avg": sum(latencies) / len(latencies) if latencies else 0,
                "p50": sorted(latencies)[len(latencies) // 2] if latencies else 0,
                "p95": sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else 0,
                "p99": sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) > 1 else 0,
            }
        }

    def clear_results(self):
        """Clear recorded results."""
        self.results = []
