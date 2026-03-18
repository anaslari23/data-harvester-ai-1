"use client";

import { useEffect, useMemo } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card } from "@/components/ui/card";
import { JobStatus } from "@/components/jobStatus";
import { StatsCards } from "@/components/statsCards";
import { useCompanyStore } from "@/store/companyStore";
import { useScraperStore } from "@/store/scraperStore";

const COLORS = ["#0b5ed7", "#2ad4ff", "#12b981", "#fb7185", "#f59e0b"];

export default function DashboardPage() {
  const { companies, fetchCompanies } = useCompanyStore();
  const { jobs, fetchJobs } = useScraperStore();

  useEffect(() => {
    void fetchCompanies();
    void fetchJobs();
  }, [fetchCompanies, fetchJobs]);

  const stats = useMemo(() => {
    const activeJobs = jobs.filter((job) => job.status === "Running").length;
    const erpCompanies = companies.filter((company) => company["Current_Use_ERP Software_Name"]).length;
    return [
      { title: "Total companies scraped", value: companies.length, note: "Unified records in the schema-guided warehouse.", icon: "companies" as const },
      { title: "Total scraping jobs", value: jobs.length, note: "Historical and current scraping executions.", icon: "jobs" as const },
      { title: "Active jobs", value: activeJobs, note: "Currently harvesting live company signals.", icon: "active" as const },
      { title: "ERP tagged companies", value: erpCompanies, note: "Detected ERP footprints across profiles and websites.", icon: "erp" as const },
    ];
  }, [companies, jobs]);

  const industryData = useMemo(() => {
    const counts = new Map<string, number>();
    companies.forEach((company) => {
      counts.set(company.Industry_Type || "Unknown", (counts.get(company.Industry_Type || "Unknown") ?? 0) + 1);
    });
    return Array.from(counts.entries()).map(([name, value]) => ({ name, value }));
  }, [companies]);

  const countryData = useMemo(() => {
    const counts = new Map<string, number>();
    companies.forEach((company) => {
      counts.set(company.country || "Unknown", (counts.get(company.country || "Unknown") ?? 0) + 1);
    });
    return Array.from(counts.entries()).map(([name, value]) => ({ name, value }));
  }, [companies]);

  const erpData = useMemo(() => {
    const counts = new Map<string, number>();
    companies.forEach((company) => {
      const name = company["Current_Use_ERP Software_Name"] || "Unspecified";
      counts.set(name, (counts.get(name) ?? 0) + 1);
    });
    return Array.from(counts.entries()).map(([name, value]) => ({ name, value }));
  }, [companies]);

  return (
    <div className="space-y-8">
      <section className="mb-4">
        <div className="mb-3 flex items-center gap-3">
          <div className="h-px w-8 bg-[#5e35b1]" />
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-[#a374ff]">Executive Overview</p>
        </div>
        <h2 className="text-4xl font-black tracking-tight text-white md:text-5xl">Intelligence Dashboard</h2>
        <p className="mt-4 max-w-2xl text-base leading-relaxed text-[#888888]">
          Track global scraping coverage, active extraction nodes, and ERP footprint intelligence from one command center.
        </p>
      </section>

      <StatsCards items={stats} />

      <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <Card>
          <div className="mb-6">
            <p className="text-sm uppercase tracking-[0.22em] text-[var(--muted-foreground)]">Industry distribution</p>
            <h3 className="mt-2 text-2xl font-semibold text-white">Companies by industry</h3>
          </div>
          <div className="h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={industryData}>
                <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                <XAxis dataKey="name" stroke="#96a6bb" tickLine={false} axisLine={false} />
                <YAxis stroke="#96a6bb" tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: "#101926", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 16 }} />
                <Bar dataKey="value" radius={[12, 12, 0, 0]} fill="#0b5ed7" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <JobStatus />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <div className="mb-6">
            <p className="text-sm uppercase tracking-[0.22em] text-[var(--muted-foreground)]">Geographic spread</p>
            <h3 className="mt-2 text-2xl font-semibold text-white">Companies by country</h3>
          </div>
          <div className="h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={countryData} layout="vertical">
                <CartesianGrid stroke="rgba(255,255,255,0.08)" horizontal={false} />
                <XAxis type="number" stroke="#96a6bb" tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="name" stroke="#96a6bb" tickLine={false} axisLine={false} width={140} />
                <Tooltip contentStyle={{ background: "#101926", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 16 }} />
                <Bar dataKey="value" radius={[0, 12, 12, 0]} fill="#2ad4ff" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <div className="mb-6">
            <p className="text-sm uppercase tracking-[0.22em] text-[var(--muted-foreground)]">ERP footprint</p>
            <h3 className="mt-2 text-2xl font-semibold text-white">ERP software usage</h3>
          </div>
          <div className="h-[320px]">
            {erpData.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={erpData} dataKey="value" nameKey="name" innerRadius={70} outerRadius={112} paddingAngle={4}>
                    {erpData.map((entry, index) => (
                      <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: "#101926", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 16 }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="grid h-full place-items-center text-center text-sm text-[var(--muted-foreground)]">ERP distribution will appear once records are scraped.</div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
