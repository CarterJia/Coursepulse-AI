"use client";

import { useEffect, useState } from "react";
import { getJobStatus } from "@/lib/api";

interface JobStatusProps {
  jobId: string;
  onComplete?: () => void;
}

export function JobStatus({ jobId, onComplete }: JobStatusProps) {
  const [status, setStatus] = useState("queued");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;
    const interval = setInterval(async () => {
      try {
        const data = await getJobStatus(jobId);
        setStatus(data.status);
        if (data.status === "succeeded") {
          clearInterval(interval);
          onComplete?.();
        }
        if (data.status === "failed") {
          clearInterval(interval);
          setError(data.error_message ?? "Unknown error");
        }
      } catch {
        /* network retry */
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [jobId, onComplete]);

  return (
    <div className="text-sm">
      <span className="font-medium">Job Status:</span>{" "}
      <span className={status === "failed" ? "text-red-600" : "text-gray-700"}>
        {status}
      </span>
      {error && <p className="text-red-500 mt-1">{error}</p>}
    </div>
  );
}
