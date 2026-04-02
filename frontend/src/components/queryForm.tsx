"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SourceSelector } from "@/components/sourceSelector";
import { useScraperStore } from "@/store/scraperStore";
import { parseQuery } from "@/services/scraperService";
import type { ScrapeSource } from "@/types/job";
import { MapPin, Briefcase, Search, Sparkles, Wand2 } from "lucide-react";
import { cn } from "@/lib/utils";

const defaultSources: ScrapeSource[] = [
  "google", "searx", "maps", "linkedin", "website",
  "indiamart", "tradeindia", "justdial",
];

type InputMode = "natural" | "structured";

export function QueryForm() {
  const { startScrape, loading, currentJob } = useScraperStore();

  const [mode, setMode] = useState<InputMode>("natural");
  const [nlText, setNlText] = useState("");
  const [parsing, setParsing] = useState(false);
  const [parsed, setParsed] = useState<{ keyword: string; location: string; industry: string } | null>(null);

  const [keyword, setKeyword] = useState("");
  const [industry, setIndustry] = useState("");
  const [location, setLocation] = useState("");
  const [sources, setSources] = useState<ScrapeSource[]>(defaultSources);

  const handleNlParse = async () => {
    if (!nlText.trim()) return;
    setParsing(true);
    try {
      const result = await parseQuery(nlText.trim());
      setParsed(result);
    } catch {
      // fallback: use the whole text as keyword
      setParsed({ keyword: nlText.trim(), location: "", industry: "" });
    } finally {
      setParsing(false);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!sources.length) return;

    if (mode === "natural") {
      // Parse first if not already parsed, then submit
      let toSubmit = parsed;
      if (!toSubmit) {
        setParsing(true);
        try {
          toSubmit = await parseQuery(nlText.trim());
          setParsed(toSubmit);
        } catch {
          toSubmit = { keyword: nlText.trim(), location: "", industry: "" };
          setParsed(toSubmit);
        } finally {
          setParsing(false);
        }
      }
      if (!toSubmit?.keyword) return;
      await startScrape({
        keyword: toSubmit.keyword,
        industry: toSubmit.industry,
        location: toSubmit.location,
        sources,
      });
    } else {
      if (!keyword.trim()) return;
      await startScrape({ keyword, industry, location, sources });
    }
  };

  const isSubmittable = mode === "natural" ? nlText.trim().length > 0 : keyword.trim().length > 0;

  return (
    <form className="space-y-8 animate-in fade-in duration-700 relative" onSubmit={handleSubmit}>

      {/* Mode toggle */}
      <div className="flex items-center gap-1 rounded-xl bg-zinc-900/60 p-1 border border-white/10 w-fit">
        <button
          type="button"
          onClick={() => { setMode("natural"); setParsed(null); }}
          className={cn(
            "flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all",
            mode === "natural"
              ? "bg-gradient-to-r from-primary to-purple-600 text-white shadow"
              : "text-white/50 hover:text-white/80",
          )}
        >
          <Wand2 className="h-3.5 w-3.5" />
          Natural Language
        </button>
        <button
          type="button"
          onClick={() => { setMode("structured"); setParsed(null); }}
          className={cn(
            "flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all",
            mode === "structured"
              ? "bg-gradient-to-r from-primary to-purple-600 text-white shadow"
              : "text-white/50 hover:text-white/80",
          )}
        >
          <Search className="h-3.5 w-3.5" />
          Structured
        </button>
      </div>

      <div className="space-y-5">
        {mode === "natural" ? (
          <div className="group relative space-y-3">
            <label className="mb-2 flex items-center gap-2 text-sm font-medium text-white/80">
              <Wand2 className="h-4 w-4 text-primary/60" />
              Describe what you want to find
            </label>
            <div className="relative">
              <div className="absolute -inset-0.5 rounded-lg bg-gradient-to-r from-primary/30 to-purple-500/30 opacity-0 blur transition duration-500 group-hover:opacity-100" />
              <textarea
                className="relative w-full rounded-lg bg-zinc-900/50 backdrop-blur-sm border border-white/10 text-base text-white p-3 min-h-[100px] resize-none transition-all focus:bg-zinc-900 focus:border-primary/50 focus:outline-none placeholder:text-white/30"
                value={nlText}
                onChange={(e) => { setNlText(e.target.value); setParsed(null); }}
                placeholder={`e.g. "Find wholesale furniture manufacturers in Mumbai"\n"Cotton textile exporters from Gujarat who supply internationally"\n"IT companies providing ERP software in Bangalore"`}
                required={mode === "natural"}
              />
            </div>

            {/* Parse preview */}
            {nlText.trim() && (
              <div className="flex items-start gap-3">
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={handleNlParse}
                  disabled={parsing}
                  className="shrink-0 border-primary/30 text-primary/80 hover:text-primary hover:border-primary/60 hover:bg-primary/5"
                >
                  {parsing ? (
                    <span className="flex items-center gap-1.5">
                      <div className="h-3 w-3 animate-spin rounded-full border border-primary/30 border-t-primary" />
                      Parsing...
                    </span>
                  ) : (
                    <span className="flex items-center gap-1.5">
                      <Sparkles className="h-3 w-3" />
                      Preview parse
                    </span>
                  )}
                </Button>

                {parsed && (
                  <div className="flex flex-wrap gap-2 text-xs">
                    <span className="rounded-full bg-primary/10 border border-primary/20 px-3 py-1 text-primary/90">
                      <span className="opacity-60">keyword: </span>{parsed.keyword || "—"}
                    </span>
                    {parsed.location && (
                      <span className="rounded-full bg-purple-500/10 border border-purple-500/20 px-3 py-1 text-purple-300/90">
                        <span className="opacity-60">location: </span>{parsed.location}
                      </span>
                    )}
                    {parsed.industry && (
                      <span className="rounded-full bg-blue-500/10 border border-blue-500/20 px-3 py-1 text-blue-300/90">
                        <span className="opacity-60">industry: </span>{parsed.industry}
                      </span>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <>
            <div className="group relative">
              <label className="mb-2 flex items-center gap-2 text-sm font-medium text-white/80 transition-colors group-hover:text-white">
                <Search className="h-4 w-4 text-primary/60" />
                Target Keyword
              </label>
              <div className="relative">
                <div className="absolute -inset-0.5 rounded-lg bg-gradient-to-r from-primary/30 to-purple-500/30 opacity-0 blur transition duration-500 group-hover:opacity-100" />
                <Input
                  className="relative bg-zinc-900/50 backdrop-blur-sm border-white/10 text-lg transition-all focus:bg-zinc-900"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  placeholder="e.g. wholesale furniture manufacturers"
                  required={mode === "structured"}
                />
              </div>
            </div>

            <div className="grid gap-5 md:grid-cols-2">
              <div className="group relative">
                <label className="mb-2 flex items-center gap-2 text-sm font-medium text-white/80 transition-colors group-hover:text-white">
                  <Briefcase className="h-4 w-4 text-primary/60" />
                  Industry
                </label>
                <Input
                  className="bg-zinc-900/50 backdrop-blur-sm border-white/10 transition-all focus:bg-zinc-900 focus:border-primary/50"
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  placeholder="e.g. retail, manufacturing"
                />
              </div>

              <div className="group relative">
                <label className="mb-2 flex items-center gap-2 text-sm font-medium text-white/80 transition-colors group-hover:text-white">
                  <MapPin className="h-4 w-4 text-primary/60" />
                  Location
                </label>
                <Input
                  className="bg-zinc-900/50 backdrop-blur-sm border-white/10 transition-all focus:bg-zinc-900 focus:border-primary/50"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="City, region, or country"
                />
              </div>
            </div>
          </>
        )}

        {/* Source selector */}
        <div>
          <div className="mb-3 flex items-center justify-between">
            <label className="text-sm font-medium text-white/80">
              Data Sources
              <span className="ml-2 text-xs text-white/40">({sources.length} selected)</span>
            </label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setSources(defaultSources)}
                className="text-xs text-primary/60 hover:text-primary transition-colors"
              >
                Reset
              </button>
              <span className="text-white/20">|</span>
              <button
                type="button"
                onClick={() => {
                  const allSources: ScrapeSource[] = [
                    "google", "searx", "maps", "linkedin", "website",
                    "direct_website", "indiamart", "tradeindia", "justdial",
                    "clutch", "goodfirms", "discovery",
                  ];
                  setSources(allSources);
                }}
                className="text-xs text-primary/60 hover:text-primary transition-colors"
              >
                Select all
              </button>
            </div>
          </div>

          <SourceSelector value={sources} onChange={setSources} />

          {sources.length === 0 && (
            <p className="mt-2 text-xs text-rose-400">Select at least one source.</p>
          )}
        </div>
      </div>

      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-white/5">
        <Button
          disabled={loading || parsing || sources.length === 0 || !isSubmittable}
          type="submit"
          className="w-full sm:w-auto px-8 bg-gradient-to-r from-primary to-purple-600 hover:from-primary/80 hover:to-purple-500/80 text-white shadow-[0_0_20px_rgba(var(--primary),0.3)] transition-all duration-300 hover:shadow-[0_0_30px_rgba(var(--primary),0.5)] hover:scale-105"
        >
          {loading || parsing ? (
            <span className="flex items-center gap-2">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/20 border-t-white" />
              {parsing ? "Parsing query..." : "Initializing Harvest..."}
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <Sparkles className="h-4 w-4" />
              Start Extraction
            </span>
          )}
        </Button>

        {currentJob ? (
          <div className="flex items-center gap-3 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 animate-in slide-in-from-right-4">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary"></span>
            </span>
            <p className="text-sm font-medium text-primary/90">
              Active Job <span className="font-bold text-primary">#{currentJob.id.split("-")[1]}</span>
            </p>
          </div>
        ) : null}
      </div>
    </form>
  );
}
