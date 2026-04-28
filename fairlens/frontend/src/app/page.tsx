"use client";

import { useState, useEffect, useRef } from "react";

type UIState = "idle" | "uploading" | "processing" | "success" | "error";

interface TaskData {
  status: string;
  step?: string;
  result?: unknown;
  error?: string;
}

interface StatusBadgeProps {
  status: string;
}

function StatusBadge({ status }: StatusBadgeProps) {
  const statusConfig: Record<string, { bg: string; text: string; label: string }> = {
    PENDING: { bg: "bg-gray-100", text: "text-gray-700", label: "Pending" },
    STARTED: { bg: "bg-blue-100", text: "text-blue-700", label: "Processing" },
    PROGRESS: { bg: "bg-blue-100", text: "text-blue-700", label: "Processing" },
    SUCCESS: { bg: "bg-green-100", text: "text-green-700", label: "Success" },
    FAILURE: { bg: "bg-red-100", text: "text-red-700", label: "Failed" },
  };

  const config = statusConfig[status] || statusConfig.PENDING;

  return (
    <span
      className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${config.bg} ${config.text}`}
    >
      {config.label}
    </span>
  );
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [uiState, setUiState] = useState<UIState>("idle");
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskData, setTaskData] = useState<TaskData | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number | null>(null);

  // Polling for task status
  useEffect(() => {
    let pollingInterval: NodeJS.Timeout | null = null;

    if (taskId && (uiState === "uploading" || uiState === "processing")) {
      pollingInterval = setInterval(async () => {
        try {
          const res = await fetch(`http://localhost:8000/status/${taskId}`);
          const data = await res.json();

          if (data.success) {
            const status = data.data.status;
            setTaskData(data.data);

            if (status === "SUCCESS") {
              setUiState("success");
              if (pollingInterval) clearInterval(pollingInterval);
            } else if (status === "FAILURE") {
              setErrorMessage(data.data.error || "Processing failed. Please try again.");
              setUiState("error");
              if (pollingInterval) clearInterval(pollingInterval);
            }
          } else {
            setErrorMessage("Failed to fetch status.");
            setUiState("error");
            if (pollingInterval) clearInterval(pollingInterval);
          }
        } catch (_err) {
          setErrorMessage("Network error. Please try again.");
          setUiState("error");
          if (pollingInterval) clearInterval(pollingInterval);
        }
      }, 1500);

      // Set 60-second timeout
      startTimeRef.current = Date.now();
      timeoutRef.current = setTimeout(() => {
        if (pollingInterval) clearInterval(pollingInterval);
        setErrorMessage("Request timed out. Please try again.");
        setUiState("error");
      }, 60000);
    }

    return () => {
      if (pollingInterval) clearInterval(pollingInterval);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [taskId, uiState]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUiState("uploading");
    setErrorMessage(null);
    setTaskData(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!data.success) {
        throw new Error(data.error?.message || "Upload failed");
      }

      setTaskId(data.data.task_id);
      setUiState("processing");
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "An error occurred.";
      setErrorMessage(errorMsg);
      setUiState("error");
    }
  };

  const handleReset = () => {
    setFile(null);
    setUiState("idle");
    setTaskId(null);
    setTaskData(null);
    setErrorMessage(null);
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white">
        <div className="max-w-3xl mx-auto px-6 py-8">
          <h1 className="text-2xl font-medium text-gray-900">FairLens</h1>
          <p className="mt-1 text-sm text-gray-600">Distributed Audit Pipeline</p>
          <p className="mt-3 text-sm text-gray-600 max-w-xl">
            Upload a dataset to run a fairness audit. The system will analyze bias,
            compute fairness metrics, and generate a detailed report.
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-3xl mx-auto px-6 py-12">
        {/* Idle State */}
        {uiState === "idle" && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-8 shadow-sm">
              <label className="block cursor-pointer">
                <div className="flex flex-col items-center justify-center py-12 px-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-gray-400 transition-colors duration-150">
                  <svg
                    className="w-10 h-10 text-gray-400 mb-3"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M12 16v-4m0 0V8m0 4h4m-4 0H8M7 20h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v11a2 2 0 002 2z"
                    />
                  </svg>
                  <p className="text-gray-700 font-medium text-center">
                    {file ? file.name : "Choose a file to upload"}
                  </p>
                  <p className="text-gray-500 text-xs text-center mt-1">
                    CSV, JSON, or other dataset formats
                  </p>
                </div>
                <input
                  type="file"
                  className="hidden"
                  onChange={handleFileSelect}
                  accept=".csv,.json,.xlsx,.xls"
                />
              </label>
            </div>

            <button
              onClick={handleUpload}
              disabled={!file}
              className="w-full px-6 py-2.5 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors duration-150"
            >
              Start Audit
            </button>
          </div>
        )}

        {/* Uploading State */}
        {uiState === "uploading" && (
          <div className="bg-white rounded-xl border border-gray-200 p-8 shadow-sm">
            <div className="flex flex-col items-center justify-center space-y-6">
              <div className="flex justify-center">
                <div className="w-10 h-10 border-3 border-gray-300 border-t-blue-600 rounded-full animate-spin"></div>
              </div>
              <div className="text-center">
                <p className="text-gray-900 font-medium">Uploading file...</p>
                <p className="text-gray-600 text-sm mt-2">Please wait while we process your dataset.</p>
              </div>
            </div>
          </div>
        )}

        {/* Processing State */}
        {uiState === "processing" && (
          <div className="bg-white rounded-xl border border-gray-200 p-8 shadow-sm">
            <div className="space-y-6">
              <div className="flex flex-col items-center justify-center space-y-4">
                <div className="flex justify-center">
                  <div className="w-10 h-10 border-3 border-gray-300 border-t-blue-600 rounded-full animate-spin"></div>
                </div>
                <div className="text-center">
                  <p className="text-gray-900 font-medium">Processing your audit...</p>
                  {taskData?.step && (
                    <p className="text-gray-600 text-sm mt-1">{taskData.step}</p>
                  )}
                </div>
              </div>

              {taskId && (
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div>
                    <p className="text-xs text-gray-600 mb-1">Task ID</p>
                    <p className="text-sm font-mono text-gray-900 break-all">{taskId}</p>
                  </div>
                  <div>
                    <StatusBadge status={taskData?.status || "PENDING"} />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Success State */}
        {uiState === "success" && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-8 shadow-sm">
              <div className="mb-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-medium text-gray-900">Audit Result</h2>
                  <StatusBadge status="SUCCESS" />
                </div>
                <p className="text-sm text-gray-600">Your fairness audit has completed successfully.</p>
              </div>

              {taskData?.result && (
                <div className="bg-gray-50 rounded-lg border border-gray-200 p-4 overflow-auto max-h-96">
                  <pre className="text-xs text-gray-700 whitespace-pre-wrap break-words font-mono">
                    {JSON.stringify(taskData.result, null, 2)}
                  </pre>
                </div>
              )}

              {taskId && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-xs text-gray-600">
                    Task ID: <span className="font-mono text-gray-900">{taskId}</span>
                  </p>
                </div>
              )}
            </div>

            <button
              onClick={handleReset}
              className="w-full px-6 py-2.5 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors duration-150"
            >
              Run Another Audit
            </button>
          </div>
        )}

        {/* Error State */}
        {uiState === "error" && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-red-200 p-8 shadow-sm">
              <div className="flex gap-4">
                <div className="flex-shrink-0 pt-1">
                  <svg
                    className="w-5 h-5 text-red-600"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div>
                  <h3 className="font-medium text-red-900 mb-1">Processing failed</h3>
                  <p className="text-sm text-red-700">{errorMessage}</p>
                </div>
              </div>

              {taskId && (
                <div className="mt-4 pt-4 border-t border-red-200">
                  <p className="text-xs text-gray-600">
                    Task ID: <span className="font-mono text-gray-900">{taskId}</span>
                  </p>
                </div>
              )}
            </div>

            <button
              onClick={handleReset}
              className="w-full px-6 py-2.5 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors duration-150"
            >
              Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
