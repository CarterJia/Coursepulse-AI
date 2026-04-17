"use client";

import { useRef, useState, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { uploadDocument } from "@/lib/api";

interface UploadFormProps {
  onUploaded?: (data: { document_id: string; job_id: string }) => void;
}

export function UploadForm({ onUploaded }: UploadFormProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setUploading(true);
      setError(null);
      try {
        const data = await uploadDocument(file);
        onUploaded?.(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Upload failed");
      } finally {
        setUploading(false);
      }
    },
    [onUploaded]
  );

  return (
    <div className="space-y-3">
      <Card
        className={`border-2 border-dashed transition-colors ${
          dragOver ? "border-indigo-500 bg-indigo-50" : "border-gray-300"
        }`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const file = e.dataTransfer.files[0];
          if (file) handleFile(file);
        }}
      >
        <CardContent className="flex flex-col items-center justify-center py-10 gap-4">
          <p className="text-gray-500 text-sm">Drop your PDF here, or click to browse</p>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFile(file);
            }}
          />
          <Button variant="outline" disabled={uploading} onClick={() => inputRef.current?.click()}>
            {uploading ? "Uploading..." : "Upload"}
          </Button>
        </CardContent>
      </Card>

      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
