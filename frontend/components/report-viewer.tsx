import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

interface Report {
  id: string;
  title: string;
  body: string;
}

interface ReportViewerProps {
  reports: Report[];
}

export function ReportViewer({ reports }: ReportViewerProps) {
  if (reports.length === 0) {
    return <p className="text-muted-foreground">No reports generated yet.</p>;
  }

  return (
    <Accordion type="multiple" defaultValue={[reports[0]?.id]} className="space-y-2">
      {reports.map((report) => (
        <AccordionItem key={report.id} value={report.id}>
          <AccordionTrigger className="text-lg font-semibold">
            {report.title}
          </AccordionTrigger>
          <AccordionContent>
            <div className="prose dark:prose-invert max-w-none whitespace-pre-wrap">
              {report.body}
            </div>
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  );
}
