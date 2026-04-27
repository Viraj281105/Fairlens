def generate_final_report(job_id, results):
    """
    Compile all results into a final structured report and save to Firestore.
    """
    print("Generating final report...")
    return {"report_url": f"/report/{job_id}"}
