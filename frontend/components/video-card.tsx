import type { Video } from "@/lib/api";

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function formatPlayCount(count: number): string {
  if (count >= 10000) {
    return `${(count / 10000).toFixed(1)}万`;
  }
  return count.toLocaleString();
}

interface VideoCardProps {
  video: Video;
}

export function VideoCard({ video }: VideoCardProps) {
  return (
    <a
      href={video.bilibili_url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex gap-3 rounded-lg border border-gray-200 p-3 hover:bg-accent transition-colors"
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={video.cover_url}
        alt={video.title}
        referrerPolicy="no-referrer"
        className="w-36 h-20 object-cover rounded border border-gray-200 shrink-0"
      />
      <div className="flex flex-col justify-between min-w-0 flex-1">
        <p className="font-medium text-sm line-clamp-2">{video.title}</p>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>{video.up_name}</span>
          <span>·</span>
          <span>{formatDuration(video.duration_seconds)}</span>
          <span>·</span>
          <span>{formatPlayCount(video.play_count)}播放</span>
        </div>
      </div>
    </a>
  );
}
