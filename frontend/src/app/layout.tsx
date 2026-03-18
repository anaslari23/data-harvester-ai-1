import type { Metadata } from "next";
import type { ReactNode } from "react";

import { Navbar } from "@/components/navbar";
import { Sidebar } from "@/components/sidebar";

import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "DataHarvester Frontend",
  description: "Company intelligence dashboard for global scraping operations.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen p-3 md:p-5">
          <div className="grid min-h-[calc(100vh-1.5rem)] gap-3 lg:grid-cols-[290px_1fr]">
            <div className="lg:sticky lg:top-5 lg:h-[calc(100vh-2.5rem)]">
              <Sidebar />
            </div>
            <div className="rounded-[32px] border border-white/5 bg-black/40 shadow-2xl backdrop-blur-2xl overflow-hidden">
              <Navbar />
              <main className="p-4 lg:p-10">{children}</main>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}
