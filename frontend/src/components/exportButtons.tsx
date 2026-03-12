"use client";

import { useState } from "react";
import { Download, FileJson, FileSpreadsheet, LoaderCircle, Sheet } from "lucide-react";

import { Button } from "@/components/ui/button";
import { pushCompaniesToSheets } from "@/services/companyService";
import type { CompanyRecord } from "@/types/company";

function downloadBlob(content: string, filename: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function toCsv(rows: CompanyRecord[]) {
  if (!rows.length) return "";
  const headers = Object.keys(rows[0]);
  return [
    headers.join(","),
    ...rows.map((row) => headers.map((header) => JSON.stringify((row as Record<string, string | undefined>)[header] ?? "")).join(",")),
  ].join("\n");
}

export function ExportButtons({ companies }: { companies: CompanyRecord[] }) {
  const [syncing, setSyncing] = useState(false);

  return (
    <div className="flex flex-wrap gap-3">
      <Button variant="outline" onClick={() => downloadBlob(toCsv(companies), "companies.csv", "text/csv;charset=utf-8;")}> 
        <Download className="mr-2 size-4" />Export CSV
      </Button>
      <Button variant="outline" onClick={() => downloadBlob(JSON.stringify(companies, null, 2), "companies.json", "application/json")}> 
        <FileJson className="mr-2 size-4" />Export JSON
      </Button>
      <Button variant="outline" onClick={() => downloadBlob(toCsv(companies), "companies.xls", "application/vnd.ms-excel")}> 
        <FileSpreadsheet className="mr-2 size-4" />Export Excel
      </Button>
      <Button
        variant="default"
        disabled={syncing || companies.length === 0}
        onClick={async () => {
          try {
            setSyncing(true);
            const result = await pushCompaniesToSheets();
            window.alert(`Synced ${result.rows_synced} rows to Google Sheets.`);
          } catch (error) {
            const message = error instanceof Error ? error.message : "Google Sheets sync failed.";
            window.alert(message);
          } finally {
            setSyncing(false);
          }
        }}
      >
        {syncing ? <LoaderCircle className="mr-2 size-4 animate-spin" /> : <Sheet className="mr-2 size-4" />}Push to Google Sheets
      </Button>
    </div>
  );
}
