"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Loader2, CheckCircle, Download, Inbox, ClipboardCheck } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { cn } from "@/lib/utils";

type ApprovedAnnotation = {
  id: string;
  original_text: string;
  corrected_language: string;
  reviewed_at?: string | null;
};

// The backend caps each page at 100 rows, so walk the pages to get them all.
const PAGE_SIZE = 100;

async function fetchAllApproved(): Promise<ApprovedAnnotation[]> {
  const all: ApprovedAnnotation[] = [];
  for (let skip = 0; ; skip += PAGE_SIZE) {
    const res = await axios.get("/api/annotations", {
      params: { approved_only: "true", skip, limit: PAGE_SIZE },
    });
    const page: ApprovedAnnotation[] = res.data.data || [];
    all.push(...page);
    if (page.length < PAGE_SIZE) return all;
  }
}

function toCsvField(value: string) {
  return /[",\r\n]/.test(value) ? `"${value.replace(/"/g, '""')}"` : value;
}

function exportCsv(rows: ApprovedAnnotation[]) {
  const lines = [
    ["annotated_phrase", "approved_correction"].join(","),
    ...rows.map((r) => [toCsvField(r.original_text), toCsvField(r.corrected_language)].join(",")),
  ];
  // Prefix a BOM so Excel opens the Sinhala script as UTF-8.
  const blob = new Blob(["﻿" + lines.join("\r\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `approved-annotations-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export default function ApprovedAnnotationsPage() {
  const [annotations, setAnnotations] = useState<ApprovedAnnotation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setAnnotations(await fetchAllApproved());
      } catch {
        toast.error("Failed to fetch approved annotations");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Approved Annotations"
        description="Corrections approved as training data. Export them as a CSV for model training."
        actions={
          <Button
            className="gap-2"
            disabled={loading || annotations.length === 0}
            onClick={() => exportCsv(annotations)}
          >
            <Download className="h-4 w-4" />
            Export CSV
          </Button>
        }
      />

      <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/40 hover:bg-muted/40">
              <TableHead className="font-semibold">Annotated Phrase</TableHead>
              <TableHead className="font-semibold w-[200px]">Approved Correction</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={2} className="h-36 text-center">
                  <Loader2 className="h-6 w-6 animate-spin mx-auto text-primary" />
                </TableCell>
              </TableRow>
            ) : annotations.length === 0 ? (
              <TableRow>
                <TableCell colSpan={2} className="h-36 text-center">
                  <div className="flex flex-col items-center gap-3 text-muted-foreground">
                    <Inbox className="h-8 w-8 opacity-40" />
                    <p className="text-sm">No approved annotations yet.</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              annotations.map((ann) => (
                <TableRow key={ann.id} className="hover:bg-muted/30">
                  <TableCell className="whitespace-normal break-words text-sm leading-relaxed">
                    {ann.original_text}
                  </TableCell>
                  <TableCell>
                    <span className={cn(
                      "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
                      "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    )}>
                      <CheckCircle className="h-3 w-3" />
                      <span className="capitalize">{ann.corrected_language}</span>
                    </span>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {annotations.length > 0 && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <ClipboardCheck className="h-3.5 w-3.5" />
          <span>{annotations.length} approved annotation{annotations.length !== 1 ? "s" : ""}.</span>
        </div>
      )}
    </div>
  );
}
