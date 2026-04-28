from celery_app import app

from backend.app.pipeline import (
    ingestion,
    schema_analysis,
    protected_attribute_detection,
    fairness_metrics,
    intersectional_analysis,
    counterfactuals,
    explanation,
    debiasing,
    report_generation
)

import logging
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def _log_with_task_id(task_id: str, job_id: str, level: str, message: str, **extra):
    """Helper to log with task_id and job_id in all messages."""
    log_msg = f"[TASK={task_id}] [JOB={job_id}] {message}"
    getattr(logger, level)(log_msg, extra=extra)

@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 5})
def run_full_audit_pipeline(self, job_id: str, dataset_id: str):
    """
    Master orchestrator task for the bias auditing pipeline.
    """
    task_id = self.request.id
    start_time = time.time()
    
    _log_with_task_id(task_id, job_id, 'info', f'TASK_STARTED: dataset_id={dataset_id}')
    
    try:
        # 1. Ingest Data
        _log_with_task_id(task_id, job_id, 'info', 'LIFECYCLE: ingestion started')
        self.update_state(state='PROGRESS', meta={'step': 'Ingestion', 'task_id': task_id, 'job_id': job_id})
        df_info = ingestion.ingest_data(dataset_id)
        _log_with_task_id(task_id, job_id, 'info', 'LIFECYCLE: ingestion completed')
        
        # 2. Schema Analysis
        _log_with_task_id(task_id, job_id, 'info', 'LIFECYCLE: schema_analysis started')
        self.update_state(state='PROGRESS', meta={'step': 'Schema Analysis', 'task_id': task_id, 'job_id': job_id})
        schema = schema_analysis.analyze_schema(df_info)
        _log_with_task_id(task_id, job_id, 'info', 'LIFECYCLE: schema_analysis completed')
        
        # 3. Detect Protected Attributes
        _log_with_task_id(task_id, job_id, 'info', 'LIFECYCLE: protected_attribute_detection started')
        self.update_state(state='PROGRESS', meta={'step': 'Detect Protected Attributes', 'task_id': task_id, 'job_id': job_id})
        protected_attrs = protected_attribute_detection.detect_protected_attributes(df_info, schema)
        _log_with_task_id(task_id, job_id, 'info', 'LIFECYCLE: protected_attribute_detection completed')
        
        # 4. Fairness Metrics
        _log_with_task_id(task_id, job_id, 'info', 'LIFECYCLE: fairness_metrics started')
        self.update_state(state='PROGRESS', meta={'step': 'Fairness Metrics', 'task_id': task_id, 'job_id': job_id})
        metrics = fairness_metrics.calculate_fairness_metrics(df_info, protected_attrs, target_col="target")
        _log_with_task_id(task_id, job_id, 'info', 'LIFECYCLE: fairness_metrics completed')
        
        # 5. Intersectional Analysis
        _log_with_task_id(task_id, job_id, 'info', 'LIFECYCLE: intersectional_analysis started')
        self.update_state(state='PROGRESS', meta={'step': 'Intersectional Analysis', 'task_id': task_id, 'job_id': job_id})
        intersection_results = intersectional_analysis.analyze_intersections(df_info, protected_attrs)
        _log_with_task_id(task_id, job_id, 'info', 'LIFECYCLE: intersectional_analysis completed')
        
        # 6. Counterfactuals
        _log_with_task_id(task_id, job_id, 'info', 'LIFECYCLE: counterfactuals started')
        self.update_state(state='PROGRESS', meta={'step': 'Counterfactuals', 'task_id': task_id, 'job_id': job_id})
        cf_results = counterfactuals.generate_counterfactuals(model=None, sample_instance=None)
        _log_with_task_id(task_id, job_id, 'info', 'LIFECYCLE: counterfactuals completed')
        
        # 7. Explanation
        _log_with_task_id(task_id, job_id, 'info', 'LIFECYCLE: explanation started')
        self.update_state(state='PROGRESS', meta={'step': 'Explanation', 'task_id': task_id, 'job_id': job_id})
        explanations = explanation.generate_explanations(metrics, cf_results)
        _log_with_task_id(task_id, job_id, 'info', 'LIFECYCLE: explanation completed')
        
        # 8. Debiasing
        _log_with_task_id(task_id, job_id, 'info', 'LIFECYCLE: debiasing started')
        self.update_state(state='PROGRESS', meta={'step': 'Debiasing', 'task_id': task_id, 'job_id': job_id})
        debiased_data = debiasing.apply_debiasing(df_info, protected_attrs)
        _log_with_task_id(task_id, job_id, 'info', 'LIFECYCLE: debiasing completed')
        
        # 9. Final Report
        _log_with_task_id(task_id, job_id, 'info', 'LIFECYCLE: report_generation started')
        self.update_state(state='PROGRESS', meta={'step': 'Report Generation', 'task_id': task_id, 'job_id': job_id})
        report = report_generation.generate_final_report(job_id, {
            "metrics": metrics,
            "intersection": intersection_results,
            "explanations": explanations,
            "debiased_data": debiased_data
        })
        _log_with_task_id(task_id, job_id, 'info', 'LIFECYCLE: report_generation completed')
        
        elapsed = time.time() - start_time
        _log_with_task_id(task_id, job_id, 'info', f'TASK_COMPLETED successfully in {elapsed:.2f}s')
        return report

    except Exception as e:
        elapsed = time.time() - start_time
        _log_with_task_id(task_id, job_id, 'error', f'TASK_FAILED after {elapsed:.2f}s: {str(e)}', exc_info=True)
        self.update_state(state='FAILURE', meta={
            'task_id': task_id,
            'job_id': job_id,
            'exc_type': type(e).__name__,
            'exc_message': str(e)
        })
        raise e
