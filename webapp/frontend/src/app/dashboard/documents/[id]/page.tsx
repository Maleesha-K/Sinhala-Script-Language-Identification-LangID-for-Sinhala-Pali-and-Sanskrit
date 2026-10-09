"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import axios from "axios";
import { toast } from "sonner";
import {
  Loader2, ArrowLeft, Languages, FileText, Download, ChevronDown, Cpu, Sparkles, Clock, XCircle, Ban, Square,
  Eye, EyeOff, ZoomIn, ZoomOut, X, ImageOff,
} from "lucide-react";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { PageHeader } from "@/components/layout/page-header";
import { apiErrorDetail, cn } from "@/lib/utils";
import { ocrEngineLabel, type OCREngine } from "@/lib/ocr-engines";
import { useLiveChannel, type LiveEvent } from "@/lib/live";
import {
  DEFAULT_CORRECTION_LANGUAGES, LanguageSummary, SegmentText, languageShares, mergeSegments, type Segment,
} from "@/components/classification/segments";
import { languageColor, languageLabel } from "@/lib/language-colors";
import { downloadCsv } from "@/lib/export";

type ModelInfo = {
  id: string;
  label: string;
  description: string;
  family: string;
  is_baseline: boolean;
  available: boolean;
  correction_languages?: string[];
};

type DocumentStatus = "uploading" | "ready" | "failed" | "deleted" | "cancelled";

type Document = {
  id: string;
  filename: string;
  upload_status: DocumentStatus;
  ocr_engine: string;
  lid_model: string | null;
  cancel_requested?: boolean;
  size_bytes: number;
  created_at: string;
};

type JobStatus = "queued" | "processing" | "completed" | "failed" | "cancelled";

/** A page's classification job, as the backend serializes it. */
type PageClassification = {
  id: string;
  status: JobStatus;
  model_name: string;
  error_message: string | null;
  cancel_requested?: boolean;
  done: number | null;
  total: number | null;
  segments: Segment[];
};

type DocumentPage = {
  id: string;
  page_number: number;
  extracted_text: string | null;
  extraction_method: string | null;
  ocr_model: string | null;
  status: "pending" | "processing" | "completed" | "failed" | "cancelled";
  classification: PageClassification | null;
};

type View = "languages" | "text";

// Whether the original page is shown beside its OCR text, remembered per browser.
const SHOW_ORIGINAL_KEY = "documents.showOriginal";
const ZOOM_STEPS = [0.5, 0.75, 1, 1.25, 1.5, 2, 3];
// The page panels fill the window below the header, so text and original can
// be read without scrolling the whole page.
const TEXT_HEIGHT = "h-[max(420px,calc(100vh_-_13rem))]";
const TEXT_MAX_HEIGHT = "max-h-[max(420px,calc(100vh_-_13rem))]";

function updateClassification(
  pages: DocumentPage[],
  pageNumber: number,
  update: (current: PageClassification | null) => PageClassification,
): DocumentPage[] {
  return pages.map((p) => (p.page_number === pageNumber ? { ...p, classification: update(p.classification) } : p));
}

export default function DocumentDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const documentId = params.id as string;

  const [document, setDocument] = useState<Document | null>(null);
  const [pages, setPages] = useState<DocumentPage[]>([]);
  const [loading, setLoading] = useState(true);
  const [settled, setSettled] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [activePageNumber, setActivePageNumber] = useState<number | null>(null);
  const [view, setView] = useState<View | null>(null);
  const [focus, setFocus] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [engines, setEngines] = useState<OCREngine[]>([]);
  // Read once; the first render is the loading screen, so the server's default
  // cannot mismatch.
  const [showOriginal, setShowOriginal] = useState(() => {
    try {
      return typeof window === "undefined" || localStorage.getItem(SHOW_ORIGINAL_KEY) !== "false";
    } catch {
      return true;
    }
  });

  const toggleOriginal = (show: boolean) => {
    setShowOriginal(show);
    try {
      localStorage.setItem(SHOW_ORIGINAL_KEY, String(show));
    } catch { /* storage unavailable: the choice lasts for this visit */ }
  };

  useEffect(() => {
    axios
      .get("/api/documents/ocr-engines")
      .then((res) => setEngines(res.data?.data ?? []))
      .catch(() => { /* fall back to raw engine ids */ });
  }, []);

  useEffect(() => {
    let cancelled = false;
    axios
      .get("/api/classification/models")
      .then((res) => {
        if (!cancelled) setModels(res.data?.data ?? []);
      })
      .catch(() => {
        if (!cancelled) toast.error("Could not load the model list.");
      })
      .finally(() => {
        if (!cancelled) setModelsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const load = useCallback(async () => {
    try {
      const [docRes, pagesRes] = await Promise.all([
        axios.get(`/api/documents/${documentId}`),
        axios.get(`/api/documents/${documentId}/pages`),
      ]);
      setDocument(docRes.data);
      setPages(pagesRes.data);
    } catch {
      toast.error("Failed to load document details");
      router.push("/dashboard/documents");
    } finally {
      setLoading(false);
    }
  }, [documentId, router]);

  useEffect(() => {
    if (documentId) load();
  }, [documentId, load]);

  // OCR pages and their classifications stream in until the server reports
  // that nothing is left to wait for.
  useLiveChannel({
    path: `/ws/documents/${documentId}`,
    enabled: !!documentId && !settled,
    load,
    onEvent: (event: LiveEvent) => {
      switch (event.type) {
        case "document":
          setDocument((prev) => (prev ? {
            ...prev,
            upload_status: event.status as DocumentStatus,
            cancel_requested: (event.cancel_requested as boolean | undefined) ?? prev.cancel_requested,
          } : prev));
          break;
        case "page": {
          const page = event.page as Omit<DocumentPage, "classification">;
          setPages((prev) => {
            const existing = prev.find((p) => p.page_number === page.page_number);
            const merged = { ...page, classification: existing?.classification ?? null };
            return existing
              ? prev.map((p) => (p.page_number === page.page_number ? merged : p))
              : [...prev, merged].sort((a, b) => a.page_number - b.page_number);
          });
          break;
        }
        case "page_job": {
          const job = event.job as Omit<PageClassification, "segments">;
          setPages((prev) => updateClassification(prev, event.page_number as number, (current) => {
            const same = current?.id === job.id;
            return {
              ...job,
              done: job.done ?? (same ? current?.done ?? null : null),
              total: job.total ?? (same ? current?.total ?? null : null),
              segments: same ? current?.segments ?? [] : [],
            };
          }));
          break;
        }
        case "page_segments": {
          const jobId = event.job_id as string;
          setPages((prev) => updateClassification(prev, event.page_number as number, (current) => {
            const base: PageClassification = current?.id === jobId
              ? current
              : { id: jobId, status: "processing", model_name: document?.lid_model ?? "", error_message: null, done: null, total: null, segments: [] };
            return { ...base, segments: mergeSegments(base.segments, event.segments as Segment[]) };
          }));
          break;
        }
        case "settled":
          setSettled(true);
          break;
      }
    },
    isFinal: (event) => event.type === "settled",
  });

  const handleIdentifyLanguage = async (modelName: string) => {
    // Combine text from all pages
    const fullText = pages
      .map(p => p.extracted_text || "")
      .filter(t => t.trim().length > 0)
      .join("\n\n");

    if (!fullText) {
      toast.error("No text found in this document to analyze.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await axios.post("/api/classification/jobs", {
        input_text: fullText,
        // OCR'd text: a printed line wrap does not end a sentence.
        segmentation_strategy: "document",
        model_name: modelName,
      });

      toast.success("Classification job created!");
      router.push(`/dashboard/classification/${res.data.data.id}`);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to start language identification");
      setSubmitting(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm("Stop processing this document? Pages read and classified so far are kept, and you are refunded for the rest.")) return;
    setCancelling(true);
    try {
      const res = await axios.post(`/api/documents/${documentId}/cancel`);
      setDocument((prev) => (prev ? { ...prev, ...res.data } : prev));
      toast.success("Cancelling: processing stops after the current page.");
    } catch (error) {
      toast.error(apiErrorDetail(error, "Failed to cancel processing"));
    } finally {
      setCancelling(false);
    }
  };

  const handleDownload = async () => {
    if (!document) return;
    try {
      const res = await axios.get(`/api/documents/${document.id}/download`);
      const { download_url } = res.data;
      const a = window.document.createElement("a");
      a.href = download_url;
      a.setAttribute("download", document.filename);
      window.document.body.appendChild(a);
      a.click();
      window.document.body.removeChild(a);
    } catch {
      toast.error("Failed to download document");
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-muted-foreground text-sm font-medium">Loading document details...</p>
      </div>
    );
  }

  if (!document) return null;

  const activePage = pages.find((p) => p.page_number === (activePageNumber ?? pages[0]?.page_number));
  const activeView: View = view ?? (activePage?.classification ? "languages" : "text");
  const totalExtractedChars = pages.reduce((acc, p) => acc + (p.extracted_text?.length || 0), 0);
  const pagesRead = pages.filter((p) => p.status === "completed" || p.status === "failed").length;
  const pagesClassified = pages.filter((p) => p.classification?.status === "completed").length;
  const pagesToClassify = pages.filter((p) => p.classification && p.classification.status !== "cancelled").length;
  const runningJobs = pages.filter(
    (p) => p.classification?.status === "queued" || p.classification?.status === "processing",
  );
  const lidModel = models.find((m) => m.id === document.lid_model);
  const correctionLanguages = lidModel?.correction_languages?.length
    ? lidModel.correction_languages
    : DEFAULT_CORRECTION_LANGUAGES;
  const processing = document.upload_status === "uploading";
  // Anything still running can be cancelled.
  const active = processing || runningJobs.length > 0;
  const cancelRequested =
    cancelling ||
    (active && !!document.cancel_requested) ||
    runningJobs.some((p) => p.classification?.cancel_requested);
  const pagesSkipped = pages.filter((p) => p.status === "cancelled").length;
  const jobsCancelled = pages.filter((p) => p.classification?.status === "cancelled").length;
  const wasCancelled = !active && (document.upload_status === "cancelled" || jobsCancelled > 0);
  const allSegments = pages.flatMap((p) => p.classification?.segments ?? []);
  const comparing = showOriginal && !!activePage;

  const exportCsv = () =>
    downloadCsv(`${document.filename.replace(/\.pdf$/i, "")}-languages.csv`, [
      ["page", "segment", "language", "confidence", "text"],
      ...pages.flatMap((p) =>
        (p.classification?.segments ?? []).map((s) => [
          p.page_number, s.segment_index + 1, languageLabel(s.predicted_language), s.confidence.toFixed(4), s.text.trim(),
        ]),
      ),
    ]);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 mb-2">
        <Button
          variant="ghost"
          size="sm"
          className="text-muted-foreground hover:text-foreground -ml-2"
          onClick={() => router.push("/dashboard/documents")}
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Documents
        </Button>
      </div>

      <PageHeader
        title={document.filename}
        description={`Uploaded on ${new Date(document.created_at).toLocaleDateString()} • ${(document.size_bytes / 1024 / 1024).toFixed(2)} MB • ${pages.length} Pages • OCR: ${ocrEngineLabel(engines, document.ocr_engine)}${lidModel ? ` • Languages: ${lidModel.label}` : ""}`}
        actions={
          <div className="flex flex-wrap items-center gap-3">
            {active && (
              <Button
                variant="outline"
                onClick={handleCancel}
                disabled={cancelRequested}
                className="gap-2 text-destructive border-destructive/30 hover:bg-destructive/5 hover:text-destructive"
              >
                {cancelRequested ? <Loader2 className="h-4 w-4 animate-spin" /> : <Square className="h-3.5 w-3.5 fill-current" />}
                {cancelRequested ? "Cancelling…" : "Cancel"}
              </Button>
            )}
            <Button variant="outline" onClick={handleDownload} className="gap-2">
              <Download className="h-4 w-4" />
              Download Original
            </Button>
            {allSegments.length > 0 && (
              <Button variant="outline" onClick={exportCsv} className="gap-2">
                <Download className="h-4 w-4" />
                Export CSV
              </Button>
            )}
            {/* base-ui DropdownMenu doesn't use asChild */}
            <DropdownMenu>
              <DropdownMenuTrigger
                disabled={submitting || processing || pages.length === 0}
                className={cn(buttonVariants({ variant: document.lid_model ? "outline" : "default" }), "gap-2", !document.lid_model && "bg-emerald-600 hover:bg-emerald-700")}
              >
                {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Languages className="h-4 w-4" />}
                {document.lid_model ? "Classify Whole Document" : "Identify Language"}
                <ChevronDown className="h-4 w-4 opacity-80" />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-72">
                <DropdownMenuGroup>
                  <DropdownMenuLabel>Choose a model</DropdownMenuLabel>
                  {modelsLoading && (
                    <div className="flex items-center gap-2 px-1.5 py-2 text-xs text-muted-foreground">
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      Loading models…
                    </div>
                  )}
                  {!modelsLoading && models.length === 0 && (
                    <div className="px-1.5 py-2 text-xs text-muted-foreground">No models available.</div>
                  )}
                  {models.map((m) => {
                    const Icon = m.is_baseline ? Cpu : Sparkles;
                    return (
                      <DropdownMenuItem
                        key={m.id}
                        disabled={!m.available}
                        onClick={() => handleIdentifyLanguage(m.id)}
                        className="items-start gap-2 py-2 cursor-pointer"
                      >
                        <Icon className="h-4 w-4 mt-0.5 text-muted-foreground" />
                        <div className="flex flex-col gap-0.5 min-w-0">
                          <span className="font-medium flex items-center gap-1.5">
                            {m.label}
                            {m.is_baseline && (
                              <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                                Baseline
                              </span>
                            )}
                          </span>
                          <span className="text-xs text-muted-foreground whitespace-normal leading-snug">
                            {m.available ? m.description : "Checkpoint not found on this machine"}
                          </span>
                        </div>
                      </DropdownMenuItem>
                    );
                  })}
                </DropdownMenuGroup>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        }
      />

      {active && (
        <div className="rounded-xl border border-primary/20 bg-primary/5 px-4 py-3 flex flex-wrap items-center gap-x-6 gap-y-1 text-sm">
          <Loader2 className="h-4 w-4 animate-spin text-primary" />
          {cancelRequested && <span className="font-medium text-amber-700">Cancelling: stopping after the current page…</span>}
          <span>
            Text: <span className="font-medium">{pagesRead}</span> of {pages.length || "?"} pages read
          </span>
          {document.lid_model && (
            <span>
              Languages: <span className="font-medium">{pagesClassified}</span> of {pagesToClassify} pages classified
            </span>
          )}
          {!cancelRequested && <span className="text-xs text-muted-foreground">Results appear below as each page finishes.</span>}
        </div>
      )}

      {wasCancelled && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-5 py-3.5 flex items-start gap-3">
          <Ban className="h-5 w-5 text-amber-600 mt-0.5 shrink-0" />
          <div className="text-sm">
            <p className="font-medium text-amber-900">Processing cancelled</p>
            <p className="text-xs text-amber-800 mt-0.5">
              {pagesRead} of {pages.length} pages were read
              {document.lid_model ? ` and ${pagesClassified} fully classified` : ""}; those results are kept below.
              {pagesSkipped > 0 && ` ${pagesSkipped} page${pagesSkipped === 1 ? " was" : "s were"} skipped.`}
              {" "}You were refunded for the work not done.
            </p>
          </div>
        </div>
      )}

      {allSegments.length > 0 && (
        <div className="rounded-xl border border-border bg-white shadow-sm px-5 py-4 space-y-3">
          <h3 className="text-sm font-semibold text-slate-800">Languages in this document</h3>
          <LanguageSummary segments={allSegments} focus={focus} onFocus={setFocus} />
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-[13rem_minmax(0,1fr)] xl:grid-cols-[15rem_minmax(0,1fr)] gap-6">
        {/* Left: page navigation, kept in view while the page panels scroll */}
        <div className="space-y-4 md:sticky md:top-0 md:self-start">
          <div className="bg-white rounded-xl border border-border overflow-hidden p-4 shadow-sm">
            <h3 className="font-semibold text-sm mb-3 text-slate-800">Document Pages</h3>
            <div className="space-y-1.5 max-h-[50vh] md:max-h-[calc(100vh_-_18rem)] overflow-y-auto pr-1 custom-scrollbar">
              {pages.map((page) => (
                <PageButton
                  key={page.page_number}
                  page={page}
                  focus={focus}
                  active={activePage?.page_number === page.page_number}
                  onClick={() => setActivePageNumber(page.page_number)}
                />
              ))}
              {pages.length === 0 && (
                <div className="text-sm text-muted-foreground text-center py-6 flex flex-col items-center gap-2">
                  {processing && <Loader2 className="h-4 w-4 animate-spin text-primary/60" />}
                  {processing ? "Preparing pages…" : "No pages extracted."}
                </div>
              )}
            </div>

            <div className="mt-4 pt-4 border-t border-slate-100">
              <div className="flex justify-between text-xs text-slate-500 mb-1">
                <span>Total Chars:</span>
                <span className="font-medium text-slate-700">{totalExtractedChars.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-xs text-slate-500">
                <span>OCR Status:</span>
                <span className="font-medium text-slate-700 capitalize">{processing ? "processing" : document.upload_status}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right side: the active page */}
        <div className="min-w-0">
          <div className="bg-white rounded-xl border border-border shadow-sm flex flex-col h-full min-h-[500px]">
            <div className="flex items-center justify-between gap-3 px-6 py-4 border-b border-border bg-slate-50/50 rounded-t-xl">
              <h2 className="font-semibold text-slate-800">
                {activePage ? `Page ${activePage.page_number}` : "Extracted Text"}
              </h2>
              <div className="flex flex-wrap items-center justify-end gap-2">
                {activePage && (
                  <button
                    onClick={() => toggleOriginal(!showOriginal)}
                    aria-pressed={showOriginal}
                    title={showOriginal ? "Hide the original page" : "Show the original page beside its text"}
                    className={cn(
                      "flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-medium transition-colors",
                      showOriginal
                        ? "border-primary/30 bg-primary/10 text-primary"
                        : "border-slate-200 bg-white text-slate-500 hover:text-slate-800",
                    )}
                  >
                    {showOriginal ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                    {showOriginal ? "Hide original" : "Show original"}
                  </button>
                )}
                {activePage?.classification && (
                  <div className="flex rounded-lg border border-slate-200 bg-white p-0.5 text-xs font-medium">
                    {(["languages", "text"] as View[]).map((v) => (
                      <button
                        key={v}
                        onClick={() => setView(v)}
                        className={cn(
                          "px-2.5 py-1 rounded-md capitalize transition-colors",
                          activeView === v ? "bg-primary/10 text-primary" : "text-slate-500 hover:text-slate-800",
                        )}
                      >
                        {v}
                      </button>
                    ))}
                  </div>
                )}
                {activePage?.ocr_model && (
                  <span className="text-xs text-slate-500 font-medium px-2 py-1 bg-white border border-slate-200 rounded-md shadow-sm">
                    Engine: {ocrEngineLabel(engines, activePage.ocr_model)}
                  </span>
                )}
              </div>
            </div>

            <div className={cn("flex-1 grid grid-cols-1", comparing && "lg:grid-cols-2")}>
            {comparing && (
              <OriginalPage
                documentId={document.id}
                pageNumber={activePage.page_number}
                onHide={() => toggleOriginal(false)}
              />
            )}
            <div className={cn("p-6 bg-[#fcfdfd] min-w-0 rounded-b-xl", comparing && "lg:rounded-bl-none")}>
              {!activePage ? (
                <Placeholder>{processing ? "Pages will appear here as they are read." : "Select a page to view extracted text."}</Placeholder>
              ) : activePage.status === "pending" ? (
                <Placeholder icon={<Clock className="h-6 w-6 text-slate-300" />}>Waiting for OCR…</Placeholder>
              ) : activePage.status === "processing" ? (
                <Placeholder icon={<Loader2 className="h-6 w-6 animate-spin text-primary/50" />}>Reading page…</Placeholder>
              ) : activePage.status === "failed" ? (
                <Placeholder className="text-red-400">OCR failed for this page. You were not charged for it.</Placeholder>
              ) : activePage.status === "cancelled" ? (
                <Placeholder icon={<Ban className="h-6 w-6 text-amber-400" />}>
                  Not read: processing was cancelled before this page. You were not charged for it.
                </Placeholder>
              ) : activeView === "languages" && activePage.classification ? (
                <PageLanguages
                  text={activePage.extracted_text}
                  classification={activePage.classification}
                  correctionLanguages={correctionLanguages}
                  focus={focus}
                />
              ) : activePage.extracted_text ? (
                <div className={cn("whitespace-pre-wrap font-mono text-sm text-slate-700 leading-relaxed custom-scrollbar overflow-y-auto", TEXT_HEIGHT)}>
                  {activePage.extracted_text}
                </div>
              ) : (
                <Placeholder icon={<FileText className="h-8 w-8 opacity-20" />}>No text found on this page.</Placeholder>
              )}
            </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Placeholder({ children, icon, className }: { children: React.ReactNode; icon?: React.ReactNode; className?: string }) {
  return (
    <div className={cn("flex flex-col items-center justify-center h-full min-h-[300px] text-slate-400 gap-3 text-sm", className)}>
      {icon}
      <p>{children}</p>
    </div>
  );
}

/** The PDF page itself, rendered by the backend, to check the OCR text against. */
function OriginalPage({
  documentId, pageNumber, onHide,
}: { documentId: string; pageNumber: number; onHide: () => void }) {
  const [zoom, setZoom] = useState(1);
  const src = `/api/documents/${documentId}/pages/${pageNumber}/image`;
  // Tracked per source, so switching pages shows the spinner again.
  const [loaded, setLoaded] = useState<string | null>(null);
  const [failed, setFailed] = useState<string | null>(null);
  const step = ZOOM_STEPS.indexOf(zoom);

  return (
    <div className="flex flex-col min-w-0 border-b lg:border-b-0 lg:border-r border-border bg-slate-100/70 lg:rounded-bl-xl">
      <div className="flex items-center justify-between gap-2 h-10 px-3 border-b border-border">
        <span className="text-xs font-medium text-slate-600">Original page</span>
        <div className="flex items-center gap-0.5 text-slate-500">
          <IconButton label="Zoom out" disabled={step <= 0} onClick={() => setZoom(ZOOM_STEPS[step - 1])}>
            <ZoomOut className="h-3.5 w-3.5" />
          </IconButton>
          <button
            onClick={() => setZoom(1)}
            title="Fit to width"
            className="w-11 text-center text-xs font-medium tabular-nums rounded-md py-1 hover:bg-white hover:text-slate-800"
          >
            {Math.round(zoom * 100)}%
          </button>
          <IconButton label="Zoom in" disabled={step >= ZOOM_STEPS.length - 1} onClick={() => setZoom(ZOOM_STEPS[step + 1])}>
            <ZoomIn className="h-3.5 w-3.5" />
          </IconButton>
          <span className="mx-1 h-4 w-px bg-slate-300" />
          <IconButton label="Hide the original page" onClick={onHide}>
            <X className="h-3.5 w-3.5" />
          </IconButton>
        </div>
      </div>
      <div className="relative h-[60vh] lg:h-[max(428px,calc(100vh_-_12.5rem))] overflow-auto custom-scrollbar p-4">
        {failed === src ? (
          <Placeholder icon={<ImageOff className="h-6 w-6 text-slate-300" />}>Could not load the original page.</Placeholder>
        ) : (
          <>
            {loaded !== src && (
              <div className="absolute inset-0 flex items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-primary/50" />
              </div>
            )}
            {/* eslint-disable-next-line @next/next/no-img-element -- an authenticated API image, not a static asset */}
            <img
              key={src}
              src={src}
              alt={`Original page ${pageNumber}`}
              onLoad={() => setLoaded(src)}
              onError={() => setFailed(src)}
              style={{ width: `${zoom * 100}%` }}
              className={cn(
                "max-w-none h-auto bg-white border border-slate-200 shadow-sm transition-opacity",
                loaded === src ? "opacity-100" : "opacity-0",
              )}
            />
          </>
        )}
      </div>
    </div>
  );
}

function IconButton({
  label, disabled, onClick, children,
}: { label: string; disabled?: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      title={label}
      className="rounded-md p-1.5 hover:bg-white hover:text-slate-800 disabled:opacity-40 disabled:pointer-events-none"
    >
      {children}
    </button>
  );
}

function PageButton({
  page, active, focus, onClick,
}: { page: DocumentPage; active: boolean; focus: string | null; onClick: () => void }) {
  const lid = page.classification;
  // The page's main language by share of its text, as in the summary.
  const shares = lid ? languageShares(lid.segments) : [];
  const language = shares[0]?.language ?? null;
  // With a language focused, pages that do not contain it fade.
  const lacksFocus = !!focus && !lid?.segments.some((s) => s.predicted_language === focus);
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full flex items-center justify-between gap-2 px-3 py-2 text-sm rounded-lg transition-all",
        active ? "bg-primary/10 text-primary font-medium" : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
        lacksFocus && "opacity-40",
      )}
    >
      <div className="flex items-center gap-2">
        <FileText className="h-4 w-4 shrink-0" />
        <span>Page {page.page_number}</span>
      </div>
      <div className="flex items-center gap-1.5">
        {page.status === "pending" && <Clock className="h-3.5 w-3.5 text-slate-300" aria-label="Waiting for OCR" />}
        {page.status === "processing" && <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" aria-label="Reading" />}
        {page.status === "cancelled" && (
          <span className="text-xs bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded-full font-medium">Skipped</span>
        )}
        {page.status === "failed" && (
          <span className="text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded-full font-medium">Failed</span>
        )}
        {page.status === "completed" && !lid && (
          <span className="text-xs bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded-full font-medium">
            {(page.extracted_text?.length || 0)} chars
          </span>
        )}
        {lid && (lid.status === "queued" || lid.status === "processing") && (
          <span className="flex items-center gap-1 text-xs text-primary">
            <Languages className="h-3.5 w-3.5" />
            {lid.status === "processing" && lid.total ? `${lid.done ?? 0}/${lid.total}` : "…"}
          </span>
        )}
        {(lid?.status === "completed" || (lid?.status === "cancelled" && lid.segments.length > 0)) && (
          <span
            className="flex items-center gap-1"
            title={shares.map((s) => `${languageLabel(s.language)} ${Math.round(s.share * 100)}%`).join(", ")}
          >
            <span className={cn(
              "text-xs px-1.5 py-0.5 rounded-full font-medium border max-w-[6.5rem] truncate",
              language ? languageColor(language).chip : "bg-slate-50 border-slate-200 text-slate-500",
            )}>
              {language ? languageLabel(language) : "No text"}
            </span>
            {shares.length > 1 && <span className="text-[10px] font-medium text-slate-400">+{shares.length - 1}</span>}
          </span>
        )}
        {lid?.status === "failed" && <XCircle className="h-3.5 w-3.5 text-destructive" aria-label="Language identification failed" />}
        {lid?.status === "cancelled" && <Ban className="h-3.5 w-3.5 text-amber-500" aria-label="Language identification cancelled" />}
      </div>
    </button>
  );
}

function PageLanguages({
  text,
  classification,
  correctionLanguages,
  focus,
}: {
  /** The page's OCR text, which its classification job classified. */
  text: string | null;
  classification: PageClassification;
  correctionLanguages: string[];
  focus: string | null;
}) {
  const { status, segments, done, total } = classification;
  const running = status === "queued" || status === "processing";
  return (
    <div className="space-y-4">
      {status === "cancelled" && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm">
          <p className="font-medium text-amber-900">Language identification cancelled for this page</p>
          <p className="text-xs text-amber-800 mt-0.5">
            {segments.length > 0
              ? `${segments.length} sentence${segments.length === 1 ? " was" : "s were"} classified first and are highlighted; the rest of the page is shown unclassified.`
              : "No sentence was classified. The page text is shown below."}
          </p>
        </div>
      )}
      {status === "failed" && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm">
          <p className="font-medium text-destructive">Language identification failed for this page</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            {classification.error_message || "An error occurred during processing."} You were not charged.
          </p>
        </div>
      )}
      {running && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
          {classification.cancel_requested
            ? "Cancelling…"
            : status === "queued"
            ? "Waiting for language identification…"
            : total ? `Classified ${done ?? segments.length} of ${total} segments` : "Classifying…"}
        </div>
      )}
      {(text || segments.length > 0) && (
        <div className={cn("leading-[2.2] text-base overflow-y-auto custom-scrollbar", TEXT_MAX_HEIGHT)}>
          <SegmentText
            text={text}
            segments={segments}
            correctionLanguages={correctionLanguages}
            running={running}
            focus={focus}
          />
        </div>
      )}
    </div>
  );
}
