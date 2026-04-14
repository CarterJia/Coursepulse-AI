import { Accordion } from "@/components/ui/accordion";
import { TopicCard } from "@/components/topic-card";
import { ReportSummary } from "@/components/report-summary";
import type { Report } from "@/lib/api";

interface ReportViewerProps {
  reports: Report[];
}

export function ReportViewer({ reports }: ReportViewerProps) {
  if (reports.length === 0) {
    return <p className="text-muted-foreground">No reports generated yet.</p>;
  }

  const by = (t: Report["section_type"]) =>
    reports.filter((r) => r.section_type === t);

  const overview = by("overview");
  const tldr = by("tldr");
  const topics = by("topic");
  const examSummary = by("exam_summary");
  const quickReview = by("quick_review");

  return (
    <div className="space-y-6">
      {/* Top zone: overview + tldr */}
      {overview.map((r) => (
        <ReportSummary key={r.id} title={r.title} body={r.body} />
      ))}
      {tldr.map((r) => (
        <ReportSummary key={r.id} title={r.title} body={r.body} variant="highlight" />
      ))}

      {/* Middle zone: topics accordion */}
      {topics.length > 0 && (
        <Accordion type="multiple" defaultValue={[topics[0].id]} className="space-y-2">
          {topics.map((r) => (
            <TopicCard key={r.id} id={r.id} title={r.title} body={r.body} />
          ))}
        </Accordion>
      )}

      {/* Bottom zone: exam_summary + quick_review */}
      {examSummary.map((r) => (
        <ReportSummary key={r.id} title={r.title} body={r.body} variant="highlight" />
      ))}
      {quickReview.map((r) => (
        <ReportSummary key={r.id} title={r.title} body={r.body} />
      ))}
    </div>
  );
}
