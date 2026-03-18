import { BriefcaseBusiness, Database, Radar, Workflow } from "lucide-react";

import { Card } from "@/components/ui/card";
import { formatNumber } from "@/lib/utils";

type StatsCardProps = {
  title: string;
  value: number;
  note: string;
  icon: "companies" | "jobs" | "active" | "erp";
};

const icons = {
  companies: Database,
  jobs: BriefcaseBusiness,
  active: Radar,
  erp: Workflow,
};

export function StatsCards({ items }: { items: StatsCardProps[] }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => {
        const Icon = icons[item.icon];
        return (
          <Card key={item.title} className="group">
            <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-[#5e35b1] to-[#a374ff] opacity-50 transition-opacity group-hover:opacity-100" />
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-[#888888]">{item.title}</p>
                <p className="mt-3 text-4xl font-bold tracking-tight text-white">{formatNumber(item.value)}</p>
                <p className="mt-2 text-xs leading-relaxed text-[#555555]">{item.note}</p>
              </div>
              <div className="flex size-12 items-center justify-center rounded-2xl border border-[#5e35b1]/20 bg-[#5e35b1]/10 transition-colors group-hover:bg-[#5e35b1]/20">
                <Icon className="size-5 text-[#a374ff]" />
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
