export type JobStatus = "Running" | "Completed" | "Failed";

export type ScrapeSource =
  | "google"
  | "maps"
  | "indiamart"
  | "tradeindia"
  | "justdial"
  | "linkedin"
  | "website"
  | "clutch"
  | "goodfirms"
  | "google_places"
  | "searx"
  | "direct_website"
  | "discovery";

export type ScrapeJob = {
  id: string;
  query: string;
  keyword: string;
  industry?: string;
  location?: string;
  status: JobStatus;
  recordsFound: number;
  startTime: string;
  progress: number;
  sources: ScrapeSource[];
};

export type StartScrapePayload = {
  keyword: string;
  industry: string;
  location: string;
  sources: ScrapeSource[];
};
