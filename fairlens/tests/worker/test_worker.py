import pytest
from unittest.mock import patch, MagicMock
from worker.tasks.orchestrator import run_full_audit_pipeline

@patch("worker.tasks.orchestrator.ingestion")
@patch("worker.tasks.orchestrator.schema_analysis")
@patch("worker.tasks.orchestrator.protected_attribute_detection")
@patch("worker.tasks.orchestrator.fairness_metrics")
@patch("worker.tasks.orchestrator.intersectional_analysis")
@patch("worker.tasks.orchestrator.counterfactuals")
@patch("worker.tasks.orchestrator.explanation")
@patch("worker.tasks.orchestrator.debiasing")
@patch("worker.tasks.orchestrator.report_generation")
def test_run_full_audit_pipeline_success(
    mock_report, mock_debiasing, mock_explanation, mock_cf, 
    mock_intersection, mock_fairness, mock_protected, mock_schema, mock_ingestion
):
    # Setup mocks
    mock_report.generate_final_report.return_value = {"status": "success", "report": "mock_report"}
    
    # Run task directly (bypassing celery delay for unit testing the logic)
    result = run_full_audit_pipeline("job_123", "dataset_456")
    
    # Assert result is the generated report
    assert result == {"status": "success", "report": "mock_report"}
    
    # Assert all steps were called
    mock_ingestion.ingest_data.assert_called_once_with("dataset_456")
    mock_schema.analyze_schema.assert_called_once()
    mock_protected.detect_protected_attributes.assert_called_once()
    mock_fairness.calculate_fairness_metrics.assert_called_once()
    mock_intersection.analyze_intersections.assert_called_once()
    mock_cf.generate_counterfactuals.assert_called_once()
    mock_explanation.generate_explanations.assert_called_once()
    mock_debiasing.apply_debiasing.assert_called_once()
    mock_report.generate_final_report.assert_called_once()

@patch("worker.tasks.orchestrator.ingestion")
def test_run_full_audit_pipeline_failure(mock_ingestion):
    # Simulate a failure in step 1
    mock_ingestion.ingest_data.side_effect = ValueError("Failed to ingest data")
    
    # Task should raise the exception so Celery catches it for retry/failure
    with pytest.raises(ValueError) as exc_info:
        run_full_audit_pipeline("job_123", "dataset_456")
        
    assert "Failed to ingest data" in str(exc_info.value)
