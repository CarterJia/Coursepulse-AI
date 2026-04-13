interface ReportViewerProps {
  title: string;
  body: string;
}

export function ReportViewer({ title, body }: ReportViewerProps) {
  return (
    <article className="prose max-w-none">
      <h2 className="text-xl font-semibold mb-3">{title}</h2>
      <div className="whitespace-pre-wrap text-gray-700">{body}</div>
    </article>
  );
}
