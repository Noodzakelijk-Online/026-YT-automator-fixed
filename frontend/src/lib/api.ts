export type Draft = {
  id: string; status: string; filename: string; file_size: number; title: string; description: string;
  tags: string[]; hashtags: string[]; seo_keywords: string[]; category_id: string; playlist_id: string | null;
  privacy_status: "private" | "unlisted" | "public"; scheduled_at: string | null; metadata_source: string;
  manually_edited: boolean; youtube_video_id: string | null; youtube_url: string | null; created_at: string;
  transcript?: { text: string; status: string; provider: string; error?: string } | null;
  thumbnails?: { id: string; source: string; selected: boolean; url: string; upload_status: string; error?: string }[];
};
export type Job = { id: string; draft_id: string; status: string; progress: number; retry_count: number; run_at: string; last_error?: string };

const configuredApiUrl = import.meta.env.VITE_API_URL?.trim();
const API_URL = (configuredApiUrl || (import.meta.env.DEV ? "http://localhost:5000/api" : "")).replace(/\/$/, "");

const configurationError = !API_URL
  ? "Backend API is not configured. Set VITE_API_URL to the deployed backend URL (for example, https://api.example.com/api) and redeploy the frontend."
  : import.meta.env.PROD && /localhost|127\.0\.0\.1|0\.0\.0\.0/i.test(API_URL)
    ? "Backend API is configured with a local address. Set VITE_API_URL to the public HTTPS backend URL and redeploy the frontend."
    : "";

export class ApiFailure extends Error {
  code: string;
  constructor(message: string, code = "request_failed") { super(message); this.code = code; }
}

async function call<T>(path: string, options?: RequestInit): Promise<T> {
  if (configurationError) throw new ApiFailure(configurationError, "api_configuration_error");

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { credentials: "include", ...options });
  } catch (error) {
    const reason = error instanceof Error && error.message ? ` (${error.message})` : "";
    throw new ApiFailure(
      `Cannot connect to the backend at ${API_URL}. Check that it is deployed, its /health endpoint is responding, and CORS_ORIGINS includes this frontend origin${reason}.`,
      "backend_unreachable",
    );
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new ApiFailure(body.error?.message || `Request failed (${response.status})`, body.error?.code);
  return body;
}

export const api = {
  url: API_URL,
  auth: () => call<{ authenticated: boolean; channel: { title: string } | null }>("/auth/status"),
  login: () => call<{ auth_url: string }>("/auth/login"),
  logout: () => call("/auth/logout", { method: "POST" }),
  settings: () => call<{ status: string; checks: Record<string, boolean> }>("/settings"),
  drafts: () => call<{ drafts: Draft[] }>("/drafts"),
  draft: (id: string) => call<{ draft: Draft }>(`/drafts/${id}`),
  createDraft: (file: File) => { const data = new FormData(); data.append("video", file); return call<{ draft: Draft }>("/drafts", { method: "POST", body: data }); },
  updateDraft: (id: string, value: Partial<Draft>) => call<{ draft: Draft }>(`/drafts/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(value) }),
  generateMetadata: (id: string) => call<{ draft: Draft }>(`/drafts/${id}/metadata/generate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" }),
  generateTranscript: (id: string) => call(`/drafts/${id}/transcript/generate`, { method: "POST" }),
  saveTranscript: (id: string, text: string) => call(`/drafts/${id}/transcript`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }) }),
  generateThumbnails: (id: string) => call(`/drafts/${id}/thumbnails/generate`, { method: "POST" }),
  selectThumbnail: (draftId: string, thumbnailId: string) => call(`/drafts/${draftId}/thumbnails/${thumbnailId}/select`, { method: "POST" }),
  jobs: () => call<{ jobs: Job[] }>("/jobs"),
  createJob: (id: string, runAt?: string) => call<{ job: Job }>(`/drafts/${id}/jobs`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ run_at: runAt || null }) }),
  batch: (draftIds: string[]) => call("/batch-jobs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ draft_ids: draftIds }) }),
  retry: (id: string) => call(`/jobs/${id}/retry`, { method: "POST" }),
  cancel: (id: string) => call(`/jobs/${id}/cancel`, { method: "POST" }),
};
