"use client";

import type { ComponentType } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, BriefcaseBusiness, Database, PlayCircle, Rows3 } from "lucide-react";

import { cn } from "@/lib/utils";

const items: { href: string; label: string; icon: ComponentType<{ className?: string }> }[] = [
  { href: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { href: "/scraper", label: "Scraper", icon: PlayCircle },
  { href: "/jobs", label: "Jobs", icon: BriefcaseBusiness },
  { href: "/results", label: "Results", icon: Rows3 },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="relative flex h-full w-full flex-col overflow-hidden rounded-[32px] border border-white/5 bg-black/40 p-6 shadow-2xl backdrop-blur-3xl">
      {/* Subtle aesthetic glow */}
      <div className="pointer-events-none absolute left-0 right-0 top-0 h-40 bg-gradient-to-b from-[#5e35b1]/15 to-transparent" />

      <div className="relative z-10 mb-12 flex items-center gap-4 px-2">
        <div className="flex size-12 items-center justify-center rounded-2xl bg-gradient-to-br from-[#5e35b1] to-indigo-600 text-lg font-black text-white shadow-lg shadow-[#5e35b1]/20">
          DH
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-tight text-white">DataHarvester</h1>
          <p className="text-xs uppercase tracking-[0.2em] text-[#888888]">Intelligence</p>
        </div>
      </div>

      <nav className="relative z-10 space-y-2">
        {items.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "group flex items-center gap-4 rounded-xl px-4 py-3.5 text-sm font-medium transition-all duration-300",
                active
                  ? "bg-white/10 text-white shadow-sm backdrop-blur-md"
                  : "text-[#888888] hover:bg-white/5 hover:text-white",
              )}
            >
              <Icon className={cn("size-5 transition-transform duration-300", active ? "text-[#a374ff] scale-110" : "group-hover:scale-110 group-hover:text-white")} />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="relative z-10 mt-auto">
        <div className="mb-6 rounded-2xl border border-white/5 bg-white/5 p-4 backdrop-blur-md transition-all hover:bg-white/10">
          <div className="mb-1 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-white/80">
            <Database className="size-3.5 text-[#a374ff]" />
            Live Throughput
          </div>
          <p className="text-2xl font-bold tracking-tight text-white">50K</p>
          <p className="mt-1 text-xs text-[#888888]">Records in virtualized view</p>
        </div>

        <div className="px-2 text-center">
          <p className="text-[10.5px] font-medium leading-[1.6] tracking-widest text-[#555555] uppercase">
            Developed by Anas<br />
            for <span className="text-[#a374ff]/90">Primacy Infotech</span> exclusively
          </p>
        </div>
      </div>
    </aside>
  );
}
