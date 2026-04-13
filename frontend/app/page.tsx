"use client";

import { useState } from "react";
import { UploadForm } from "@/components/upload-form";
import { JobStatus } from "@/components/job-status";
import { DocumentList } from "@/components/document-list";

export default function HomePage() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [docId, setDocId] = useState<string | null>(null);

  return (
    <main className="max-w-2xl mx-auto py-12 px-4 space-y-8">
      <div>
        <h1 className="text-3xl font-bold mb-2">CoursePulse AI</h1>
        <p className="text-muted-foreground">Upload your course slides to generate a structured teaching report.</p>
      </div>

      <UploadForm
        onUploaded={(data) => {
          setDocId(data.document_id);
          setJobId(data.job_id);
        }}
      />

      {jobId && (
        <JobStatus jobId={jobId} onComplete={() => {
          if (docId) window.location.href = `/documents/${docId}`;
        }} />
      )}

      <DocumentList />
    </main>
  );
}
