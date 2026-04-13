"use client";

import { useParams } from "next/navigation";

export default function DocumentDetailPage() {
  const params = useParams();
  const id = params.id as string;

  return (
    <main className="max-w-4xl mx-auto py-12 px-4">
      <h1 className="text-2xl font-bold mb-4">Document Report</h1>
      <p className="text-gray-500">Document ID: {id}</p>
      <p className="mt-4 text-gray-600">Report content will appear here after processing.</p>
    </main>
  );
}
