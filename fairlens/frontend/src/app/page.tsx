"use client";

import { useState, useEffect } from "react";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [step, setStep] = useState<string | null>(null);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (taskId && status !== "SUCCESS" && status !== "FAILURE") {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`http://localhost:8000/status/${taskId}`);
          const data = await res.json();
          if (data.success) {
            setStatus(data.data.status);
            if (data.data.status === "PROGRESS") {
              setStep(data.data.step);
            } else if (data.data.status === "SUCCESS") {
              setResult(data.data.result);
              setStep("Completed");
            } else if (data.data.status === "FAILURE") {
              setError(data.data.error || "Processing failed. Please try again.");
              setStep("Failed");
            }
          } else {
            setError("Failed to fetch status.");
            setStatus("FAILURE");
          }
        } catch (err) {
          setError("Network error. Please try again.");
          setStatus("FAILURE");
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [taskId, status]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    setResult(null);
    setTaskId(null);
    setStatus("UPLOADING");
    setStep("Uploading file...");

    try {
      // 1. Upload File
      const formData = new FormData();
      formData.append("file", file);
      const uploadRes = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });
      const uploadData = await uploadRes.json();
      
      if (!uploadData.success) throw new Error(uploadData.error?.message || "Upload failed");

      // 2. Start Audit
      setStep("Starting audit...");
      const startRes = await fetch("http://localhost:8000/audit/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dataset_id: uploadData.data.dataset_id }),
      });
      const startData = await startRes.json();
      
      if (!startData.success) throw new Error(startData.error?.message || "Start audit failed");
      
      setTaskId(startData.data.task_id);
      setStatus("PENDING");
      setStep("Waiting for worker...");
      
    } catch (err: any) {
      setError(err.message || "An error occurred.");
      setStatus("FAILURE");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl w-full space-y-8 bg-white p-10 rounded-xl shadow-lg border border-gray-200">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            FairLens Bias Auditing
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Upload a dataset to run the fairness pipeline
          </p>
        </div>
        
        <div className="mt-8 space-y-6">
          <div className="flex items-center justify-center w-full">
            <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100">
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <p className="mb-2 text-sm text-gray-500"><span className="font-semibold">Click to upload</span> or drag and drop</p>
                    <p className="text-xs text-gray-500">{file ? file.name : "CSV files only"}</p>
                </div>
                <input type="file" className="hidden" accept=".csv" onChange={handleFileChange} />
            </label>
          </div>
          
          <button
            onClick={handleUpload}
            disabled={!file || uploading || (status !== null && status !== "FAILURE" && status !== "SUCCESS")}
            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none disabled:bg-gray-400"
          >
            {uploading ? "Uploading..." : "Start Audit"}
          </button>
        </div>

        {status && (
          <div className="mt-8 border-t border-gray-200 pt-8">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Status: {status}</h3>
            {step && <p className="mt-1 text-sm text-gray-500">Current Step: {step}</p>}
            
            {(status === "PENDING" || status === "PROGRESS" || status === "STARTED" || status === "UPLOADING") ? (
                <div className="mt-4 flex justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                </div>
            ) : null}

            {error && (
              <div className="mt-4 bg-red-50 border-l-4 border-red-400 p-4">
                <div className="flex">
                  <div className="ml-3">
                    <p className="text-sm text-red-700">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {result && (
              <div className="mt-4 bg-green-50 border-l-4 border-green-400 p-4">
                 <h4 className="text-md font-semibold text-green-800 mb-2">Audit Complete</h4>
                 <pre className="text-xs text-green-700 bg-green-100 p-4 rounded overflow-auto max-h-96">
                    {JSON.stringify(result, null, 2)}
                 </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
