import { api } from "@/services/api";
import type { ScrapeJob, StartScrapePayload } from "@/types/job";

export async function startScrape(payload: StartScrapePayload) {
  const { data } = await api.post<ScrapeJob>("/api/start-scrape", payload);
  return data;
}

export async function getJobs() {
  const { data } = await api.get<ScrapeJob[]>("/api/jobs");
  return data;
}

export async function clearJobs() {
  const { data } = await api.delete<{ cleared: boolean }>("/api/jobs");
  return data;
}

export async function parseQuery(text: string): Promise<{ keyword: string; location: string; industry: string }> {
  const { data } = await api.post("/api/parse-query", { text });
  return data;
}

export async function uploadParams(file: File, sources: string) {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await api.post<{ job: ScrapeJob; parsed_rows: number }>(
    `/api/upload-params?sources=${encodeURIComponent(sources)}`,
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 60_000, // files can take longer to parse
    },
  );
  return data;
}
