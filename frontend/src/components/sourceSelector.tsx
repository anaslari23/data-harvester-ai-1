"use client";

import * as Checkbox from "@radix-ui/react-checkbox";
import { Check } from "lucide-react";

import type { ScrapeSource } from "@/types/job";
import { cn } from "@/lib/utils";

const sourceOptions: { value: ScrapeSource; label: string; description?: string }[] = [
  { value: "google", label: "Google Search", description: "DuckDuckGo/Google web results" },
  { value: "searx", label: "Searx", description: "Federated multi-engine search" },
  { value: "maps", label: "Google Maps", description: "Local business listings" },
  { value: "linkedin", label: "LinkedIn", description: "Company & professional profiles" },
  { value: "website", label: "Company Websites", description: "Direct website scraping" },
  { value: "direct_website", label: "Direct Web Scrape", description: "Deep-crawl target sites" },
  { value: "indiamart", label: "IndiaMART", description: "Indian B2B marketplace" },
  { value: "tradeindia", label: "TradeIndia", description: "Indian trade directory" },
  { value: "justdial", label: "JustDial", description: "Indian business directory" },
  { value: "clutch", label: "Clutch", description: "Agency & service provider ratings" },
  { value: "goodfirms", label: "GoodFirms", description: "Software & IT companies" },
  { value: "google_places", label: "Google Places API", description: "Requires API key" },
  { value: "discovery", label: "AI Discovery", description: "Smart directory discovery" },
];

export function SourceSelector({ value, onChange }: { value: ScrapeSource[]; onChange: (sources: ScrapeSource[]) => void }) {
  const toggle = (source: ScrapeSource) => {
    onChange(value.includes(source) ? value.filter((item) => item !== source) : [...value, source]);
  };

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      {sourceOptions.map((source) => {
        const checked = value.includes(source.value);
        return (
          <label
            key={source.value}
            className={cn(
              "flex cursor-pointer items-center justify-between rounded-2xl border px-4 py-3 text-sm transition",
              checked ? "border-[var(--accent)] bg-[var(--accent)]/10 text-white" : "border-white/10 bg-white/5 text-[var(--muted-foreground)]",
            )}
          >
            <span className="flex flex-col gap-0.5">
              <span className="font-medium">{source.label}</span>
              {source.description && (
                <span className="text-xs opacity-50">{source.description}</span>
              )}
            </span>
            <Checkbox.Root
              checked={checked}
              onCheckedChange={() => toggle(source.value)}
              className="grid size-5 place-items-center rounded-md border border-white/20 bg-black/20 shrink-0"
            >
              <Checkbox.Indicator>
                <Check className="size-4 text-[var(--accent-soft)]" />
              </Checkbox.Indicator>
            </Checkbox.Root>
          </label>
        );
      })}
    </div>
  );
}
