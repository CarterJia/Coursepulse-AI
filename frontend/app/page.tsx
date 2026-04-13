"use client";

import { useState } from "react";
import { UploadForm } from "@/components/upload-form";
import { JobStatus } from "@/components/job-status";

export default function HomePage() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [docId, setDocId] = useState<string | null>(null);

  return (
    <main className="max-w-2xl mx-auto py-12 px-4">
      <h1 className="text-3xl font-bold mb-6">CoursePulse AI</h1>
      <p className="mb-8 text-gray-600">Upload your course slides to generate a structured teaching report.</p>

      <UploadForm
        onUploaded={(data) => {
          setDocId(data.document_id);
          setJobId(data.job_id);
        }}
      />

      {jobId && (
        <div className="mt-6">
          <JobStatus jobId={jobId} onComplete={() => {
            if (docId) window.location.href = `/documents/${docId}`;
          }} />
        </div>
      )}
    </main>
  );
}
