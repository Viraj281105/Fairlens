from worker.celery_app import app
import sys
import os

# Ensure pipeline modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline import (
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

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 5})
def run_full_audit_pipeline(self, job_id: str, dataset_id: str):
    """
    Master orchestrator task for the bias auditing pipeline.
    """
    logger.info(f"Starting audit pipeline for job: {job_id}, dataset: {dataset_id}")
    
    try:
        # 1. Ingest Data
        self.update_state(state='PROGRESS', meta={'step': 'Ingestion'})
        df_info = ingestion.ingest_data(dataset_id)
        
        # 2. Schema Analysis
        self.update_state(state='PROGRESS', meta={'step': 'Schema Analysis'})
        schema = schema_analysis.analyze_schema(df_info)
        
        # 3. Detect Protected Attributes
        self.update_state(state='PROGRESS', meta={'step': 'Detect Protected Attributes'})
        protected_attrs = protected_attribute_detection.detect_protected_attributes(df_info, schema)
        
        # 4. Fairness Metrics
        self.update_state(state='PROGRESS', meta={'step': 'Fairness Metrics'})
        metrics = fairness_metrics.calculate_fairness_metrics(df_info, protected_attrs, target_col="target")
        
        # 5. Intersectional Analysis
        self.update_state(state='PROGRESS', meta={'step': 'Intersectional Analysis'})
        intersection_results = intersectional_analysis.analyze_intersections(df_info, protected_attrs)
        
        # 6. Counterfactuals
        self.update_state(state='PROGRESS', meta={'step': 'Counterfactuals'})
        cf_results = counterfactuals.generate_counterfactuals(model=None, sample_instance=None)
        
        # 7. Explanation
        self.update_state(state='PROGRESS', meta={'step': 'Explanation'})
        explanations = explanation.generate_explanations(metrics, cf_results)
        
        # 8. Debiasing
        self.update_state(state='PROGRESS', meta={'step': 'Debiasing'})
        debiased_data = debiasing.apply_debiasing(df_info, protected_attrs)
        
        # 9. Final Report
        self.update_state(state='PROGRESS', meta={'step': 'Report Generation'})
        report = report_generation.generate_final_report(job_id, {
            "metrics": metrics,
            "intersection": intersection_results,
            "explanations": explanations,
            "debiased_data": debiased_data
        })
        
        logger.info(f"Pipeline complete for job {job_id}.")
        return report

    except Exception as e:
        logger.error(f"Pipeline failed for job {job_id}: {str(e)}", exc_info=True)
        # Update state so that failure can be queried cleanly
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e
