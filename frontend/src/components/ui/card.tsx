import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-[24px] border border-white/5 bg-black/40 p-6 shadow-2xl backdrop-blur-2xl transition-all duration-300 hover:border-white/10 hover:bg-black/50",
        className,
      )}
      {...props}
    />
  );
}
