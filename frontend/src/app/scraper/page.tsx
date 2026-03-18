import { JobStatus } from "@/components/jobStatus";
import { QueryForm } from "@/components/queryForm";
import { BulkUpload } from "@/components/bulkUpload";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Sparkles, Globe2, FileUp, Search } from "lucide-react";

export default function ScraperPage() {
  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <section className="relative">
        <div className="absolute -left-4 top-0 h-14 w-1 rounded-r-full bg-gradient-to-b from-[#5e35b1] to-[#a374ff] shadow-[0_0_15px_rgba(163,116,255,0.4)]" />
        
        <div className="flex items-center gap-3">
          <Globe2 className="size-5 animate-pulse text-[#a374ff]" />
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-[#a374ff]">
            Extraction Engine
          </p>
        </div>
        
        <h2 className="mt-3 text-4xl font-black tracking-tight text-white md:text-5xl">
          Harvest <span className="bg-gradient-to-r from-[#5e35b1] to-[#a374ff] bg-clip-text text-transparent">Global Data</span>
        </h2>
        
        <p className="mt-4 max-w-2xl text-base leading-relaxed text-[#888888]">
          Deploy AI-powered extraction agents to seamlessly gather company profiles, decision-makers, and market intelligence across the web.
        </p>
      </section>

      <div className="grid gap-8 xl:grid-cols-[1.3fr_0.8fr]">
        <div className="space-y-6">
          <Tabs defaultValue="single" className="w-full">
            <TabsList className="grid h-12 w-full max-w-[400px] grid-cols-2 rounded-2xl border border-white/5 bg-white/5 p-1">
              <TabsTrigger value="single" className="rounded-xl transition-all data-[state=active]:bg-[#5e35b1] data-[state=active]:text-white data-[state=active]:shadow-lg data-[state=inactive]:text-[#888888]">
                <Search className="mr-2 size-4" />
                Single Search
              </TabsTrigger>
              <TabsTrigger value="bulk" className="rounded-xl transition-all data-[state=active]:bg-[#5e35b1] data-[state=active]:text-white data-[state=active]:shadow-lg data-[state=inactive]:text-[#888888]">
                <FileUp className="mr-2 size-4" />
                Bulk Upload
              </TabsTrigger>
            </TabsList>

            <TabsContent value="single" className="mt-6">
              <Card>
                <div className="relative p-2 sm:p-4">
                  <div className="mb-8 flex items-center gap-4">
                    <div className="rounded-xl border border-[#5e35b1]/30 bg-[#5e35b1]/10 p-3 shadow-inner">
                      <Sparkles className="size-5 text-[#a374ff]" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold tracking-tight text-white">Extraction Parameters</h3>
                      <p className="text-sm text-[#888888]">Define your target criteria below</p>
                    </div>
                  </div>
                  <QueryForm />
                </div>
              </Card>
            </TabsContent>

            <TabsContent value="bulk" className="mt-6">
              <Card>
                <div className="relative p-2 sm:p-4">
                  <div className="mb-8 flex items-center gap-4">
                    <div className="rounded-xl border border-[#5e35b1]/30 bg-[#5e35b1]/10 p-3 shadow-inner">
                      <FileUp className="size-5 text-[#a374ff]" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold tracking-tight text-white">Bulk Data Import</h3>
                      <p className="text-sm text-[#888888]">Upload your JSON or CSV parameter file</p>
                    </div>
                  </div>
                  <BulkUpload />
                </div>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
        
        <div className="xl:sticky xl:top-24 h-fit">
          <JobStatus />
        </div>
      </div>
    </div>
  );
}
