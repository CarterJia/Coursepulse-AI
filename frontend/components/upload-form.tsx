"use client";

import { useRef, useState } from "react";

interface UploadFormProps {
  onUploaded?: (data: { document_id: string; job_id: string }) => void;
}

export function UploadForm({ onUploaded }: UploadFormProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const file = inputRef.current?.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/api/documents/upload`,
        { method: "POST", body: (() => { const fd = new FormData(); fd.append("file", file); return fd; })() }
      );
      const data = await res.json();
      onUploaded?.(data);
    } finally {
      setUploading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <input ref={inputRef} type="file" accept=".pdf,.pptx,.png,.jpg,.jpeg" />
      <button type="submit" disabled={uploading} className="px-4 py-2 bg-blue-600 text-white rounded">
        {uploading ? "Uploading..." : "Upload"}
      </button>
    </form>
  );
}
