"use client";

import { Search, Bell, UserCircle2 } from "lucide-react";

import { Input } from "@/components/ui/input";

export function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-white/5 bg-black/40 backdrop-blur-2xl">
      <div className="flex h-20 items-center justify-between gap-6 px-4 md:px-10">
        <div className="relative max-w-xl flex-1">
          <Search className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-[#888888]" />
          <Input 
            className="h-11 rounded-full border-white/5 bg-white/5 pl-11 text-sm text-white transition-all placeholder:text-[#555555] focus-visible:bg-white/10 focus-visible:ring-1 focus-visible:ring-[#a374ff]/50" 
            placeholder="Search Intelligence Graph..." 
          />
        </div>
        <div className="flex items-center gap-4">
          <button className="group relative rounded-full border border-white/5 bg-white/5 p-2.5 text-[#888888] transition-all hover:bg-white/10 hover:text-white">
            <div className="absolute right-2.5 top-2.5 h-1.5 w-1.5 rounded-full bg-[#a374ff] ring-2 ring-black" />
            <Bell className="size-4.5 transition-transform group-hover:scale-110" />
          </button>
          <div className="flex cursor-pointer items-center gap-3 rounded-full border border-white/5 bg-white/5 p-1.5 pr-5 transition-all hover:bg-white/10">
            <div className="flex size-9 items-center justify-center rounded-full bg-gradient-to-br from-[#5e35b1] to-indigo-600 shadow-inner">
              <UserCircle2 className="size-5 text-white" />
            </div>
            <div className="hidden text-left sm:block">
              <p className="text-sm font-bold tracking-tight text-white">Analyst Console</p>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[#a374ff]">Global Data Team</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
