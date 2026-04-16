"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { listDocuments } from "@/lib/api";

interface Doc {
  id: string;
  filename: string;
  mime_type: string;
  created_at: string;
}

export function DocumentList() {
  const [docs, setDocs] = useState<Doc[]>([]);

  useEffect(() => {
    listDocuments().then(setDocs).catch(() => {});
  }, []);

  if (docs.length === 0) return null;

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold">Your Documents</h2>
      {docs.map((doc) => (
        <Link key={doc.id} href={`/documents/${doc.id}`}>
          <Card className="hover:bg-muted/50 transition-colors cursor-pointer">
            <CardContent className="flex items-center justify-between py-3">
              <span className="font-medium">{doc.filename}</span>
              <Badge variant="secondary">{doc.mime_type.split("/")[1]?.toUpperCase()}</Badge>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}
