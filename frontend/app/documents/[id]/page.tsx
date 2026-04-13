"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ReportViewer } from "@/components/report-viewer";
import { GlossaryPanel } from "@/components/glossary-panel";
import { Skeleton } from "@/components/ui/skeleton";
import { getDocument, getGlossary } from "@/lib/api";

export default function DocumentDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [doc, setDoc] = useState<any>(null);
  const [glossary, setGlossary] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getDocument(id), getGlossary(id)])
      .then(([d, g]) => { setDoc(d); setGlossary(g); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <main className="max-w-4xl mx-auto py-12 px-4 space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </main>
    );
  }

  if (!doc) {
    return <main className="max-w-4xl mx-auto py-12 px-4"><p>Document not found.</p></main>;
  }

  return (
    <main className="max-w-4xl mx-auto py-12 px-4">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">{doc.filename}</h1>
          <p className="text-sm text-muted-foreground">Uploaded {new Date(doc.created_at).toLocaleDateString()}</p>
        </div>
        <GlossaryPanel entries={glossary} />
      </div>
      <ReportViewer reports={doc.reports ?? []} />
    </main>
  );
}
