const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type SectionType =
  | "overview"
  | "tldr"
  | "topic"
  | "exam_summary"
  | "quick_review";

export interface Report {
  id: string;
  title: string;
  body: string;
  section_type: SectionType;
}

export async function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/documents/upload`, {
    method: "POST",
    body: formData,
  });
  return res.json();
}

export async function getJobStatus(jobId: string) {
  const res = await fetch(`${API_BASE}/api/jobs/${jobId}`);
  return res.json();
}

export async function listDocuments() {
  const res = await fetch(`${API_BASE}/api/documents`);
  return res.json();
}

export async function getDocument(id: string) {
  const res = await fetch(`${API_BASE}/api/documents/${id}`);
  return res.json();
}

export async function getGlossary(documentId: string) {
  const res = await fetch(`${API_BASE}/api/documents/${documentId}/glossary`);
  return res.json();
}

export interface Video {
  bvid: string;
  title: string;
  bilibili_url: string;
  cover_url: string;
  up_name: string;
  duration_seconds: number;
  play_count: number;
  similarity_score: number;
}

export interface TopicVideos {
  topic_title: string;
  videos: Video[];
}

export async function getVideos(documentId: string): Promise<TopicVideos[]> {
  const res = await fetch(`${API_BASE}/api/documents/${documentId}/videos`);
  if (!res.ok) return [];
  return res.json();
}

export async function uploadAssignment(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/assignments/upload`, {
    method: "POST",
    body: formData,
  });
  return res.json();
}
