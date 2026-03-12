"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

import { sanitizeInput } from "@/lib/utils";
import { getJobs, startScrape } from "@/services/scraperService";
import type { ScrapeJob, StartScrapePayload } from "@/types/job";

type ScraperState = {
  currentJob: ScrapeJob | null;
  jobStatus: ScrapeJob["status"] | "Idle";
  progress: number;
  jobs: ScrapeJob[];
  loading: boolean;
  error: string | null;
  startScrape: (payload: StartScrapePayload) => Promise<void>;
  fetchJobs: () => Promise<void>;
};

export const useScraperStore = create<ScraperState>()(
  persist(
    (set) => ({
      currentJob: null,
      jobStatus: "Idle",
      progress: 0,
      jobs: [],
      loading: false,
      error: null,
      startScrape: async (payload) => {
        const safePayload = {
          ...payload,
          keyword: sanitizeInput(payload.keyword),
          industry: sanitizeInput(payload.industry),
          location: sanitizeInput(payload.location),
        };

        set({ loading: true, error: null });
        try {
          const job = await startScrape(safePayload);
          set((state) => ({
            currentJob: job,
            jobStatus: job.status,
            progress: job.progress,
            jobs: [job, ...state.jobs.filter((existing) => existing.id !== job.id)],
            loading: false,
          }));
        } catch (error) {
          set({
            loading: false,
            error: error instanceof Error ? error.message : "Unable to start scrape job.",
          });
        }
      },
      fetchJobs: async () => {
        set({ loading: true, error: null });
        try {
          const jobs = await getJobs();
          const currentJob = jobs[0] ?? null;
          set({
            jobs,
            currentJob,
            jobStatus: currentJob?.status ?? "Idle",
            progress: currentJob?.progress ?? 0,
            loading: false,
          });
        } catch (error) {
          set({
            jobs: [],
            currentJob: null,
            jobStatus: "Idle",
            progress: 0,
            loading: false,
            error: error instanceof Error ? error.message : "Unable to load jobs.",
          });
        }
      },
    }),
    {
      name: "dh-scraper-store-v2",
      partialize: (state) => ({
        currentJob: state.currentJob,
        jobStatus: state.jobStatus,
        progress: state.progress,
        jobs: state.jobs,
      }),
    },
  ),
);
