import {
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { MarkdownRenderer } from "@/components/markdown-renderer";
import { VideoCard } from "@/components/video-card";
import type { Video } from "@/lib/api";

interface TopicCardProps {
  id: string;
  title: string;
  body: string;
  videos?: Video[];
}

export function TopicCard({ id, title, body, videos = [] }: TopicCardProps) {
  return (
    <AccordionItem value={id}>
      <AccordionTrigger className="text-lg font-semibold">{title}</AccordionTrigger>
      <AccordionContent>
        <MarkdownRenderer content={body} />
        {videos.length > 0 && (
          <div className="mt-6 pt-4 border-t space-y-3">
            <p className="text-sm font-medium text-muted-foreground">相关视频推荐</p>
            {videos.map((v) => (
              <VideoCard key={v.bvid} video={v} />
            ))}
          </div>
        )}
      </AccordionContent>
    </AccordionItem>
  );
}
