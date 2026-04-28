# FairLens Bias Auditing - Demo Script

This script provides step-by-step instructions to run a live demonstration of the FairLens pipeline. The system has been hardened for production-level stability and clear UX.

## 1. Prerequisites

Ensure Docker is running on your machine.

Start the system from the `infra` directory:
```bash
cd infra
docker compose up --build -d
```

Verify that all services are healthy and running:
```bash
docker compose ps
```

You can optionally check the health endpoint:
```bash
curl http://localhost:8000/health
```
Expected Output:
```json
{
  "status": "ok",
  "services": {
    "api": "up",
    "redis": "up",
    "worker": "up"
  }
}
```

## 2. Running the Demo (UI)

1. Open your browser and navigate to the frontend application:
   [http://localhost:3000](http://localhost:3000)

2. **Upload Dataset**: 
   Click on the upload area and select a dummy CSV dataset (or drag-and-drop it).

3. **Start Audit**:
   Click the **Start Audit** button.

4. **Observe the Flow**:
   - The UI will immediately switch to the `UPLOADING` state.
   - Once uploaded, it triggers the audit pipeline and switches to `PENDING`.
   - The worker picks up the job. The UI polls the `GET /status/{task_id}` endpoint every 2 seconds.
   - You will see the UI dynamically update the "Current Step" as it progresses through the pipeline (Ingestion -> Schema Analysis -> ... -> Report Generation).
   - *Note: If you want to show the judges the backend processing, you can split your screen and run `docker compose logs -f worker`.*

5. **Completion**:
   Once the task is completed, the status turns to `SUCCESS` and the final audit JSON report is gracefully displayed on the screen.

## 3. Fallback / Failure Demo

If you want to demonstrate how the system gracefully handles failures (e.g., a corrupted file or worker crash):

1. Submit an invalid file format (or intentionally break the worker logic).
2. The UI will catch the failure state from the polling endpoint.
3. Instead of crashing or showing a white screen, the UI will display a red alert box:
   `Processing failed. Please try again.`
4. Judges will appreciate the robust error handling without exposing stack traces to the end user.

## 4. Flower Monitoring (Optional)

You can demonstrate that you have enterprise-grade observability by opening the Flower dashboard:
[http://localhost:5555](http://localhost:5555)

Show the judges the real-time processing of Celery tasks, including execution times and success/failure rates.
