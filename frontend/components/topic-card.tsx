import {
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { MarkdownRenderer } from "@/components/markdown-renderer";

interface TopicCardProps {
  id: string;
  title: string;
  body: string;
}

export function TopicCard({ id, title, body }: TopicCardProps) {
  return (
    <AccordionItem value={id}>
      <AccordionTrigger className="text-lg font-semibold">{title}</AccordionTrigger>
      <AccordionContent>
        <MarkdownRenderer content={body} />
      </AccordionContent>
    </AccordionItem>
  );
}
