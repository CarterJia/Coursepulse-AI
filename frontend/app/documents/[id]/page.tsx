"use client";

import { useParams } from "next/navigation";
import { ReportViewer } from "@/components/report-viewer";
import { GlossaryPanel } from "@/components/glossary-panel";

export default function DocumentDetailPage() {
  const params = useParams();
  const id = params.id as string;

  // Placeholder data; replaced by API calls once backend wires up reports
  const report = { title: "Document Report", body: "Report content will appear here after processing." };
  const glossary: { term: string; definition: string; analogy?: string }[] = [];

  return (
    <main className="max-w-5xl mx-auto py-12 px-4">
      <p className="text-sm text-gray-400 mb-4">Document ID: {id}</p>
      <div className="flex gap-8">
        <div className="flex-1">
          <ReportViewer title={report.title} body={report.body} />
        </div>
        <GlossaryPanel entries={glossary} />
      </div>
    </main>
  );
}
