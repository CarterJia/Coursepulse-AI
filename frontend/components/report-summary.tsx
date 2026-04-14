import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MarkdownRenderer } from "@/components/markdown-renderer";

interface ReportSummaryProps {
  title: string;
  body: string;
  variant?: "default" | "highlight";
}

export function ReportSummary({ title, body, variant = "default" }: ReportSummaryProps) {
  const borderClass =
    variant === "highlight" ? "border-2 border-amber-400" : "";
  return (
    <Card className={borderClass}>
      <CardHeader>
        <CardTitle className="text-xl">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <MarkdownRenderer content={body} />
      </CardContent>
    </Card>
  );
}
