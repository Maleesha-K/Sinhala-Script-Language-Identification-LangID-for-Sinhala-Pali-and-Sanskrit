"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import axios from "axios";
import { toast } from "sonner";
import {
  ArrowLeft, Loader2, CheckCircle2, XCircle, AlertTriangle, Clock, Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useAuth } from "@/context/auth-context";
import { cn } from "@/lib/utils";

type Segment = {
  id: string;
  segment_index: number;
  text: string;
  predicted_language: string;
  confidence: number;
  probabilities?: Record<string, number>;
};

type JobData = {
  id: string;
  status: "queued" | "processing" | "completed" | "failed";
  segmentation_strategy: string;
  total_tokens: number;
  segments?: Segment[];
};

const LANG_STYLES: Record<string, { bg: string; border: string; text: string; label: string }> = {
  sinhala:  { bg: "bg-blue-50",   border: "border-blue-300",  text: "text-blue-800",  label: "Sinhala" },
  pali:     { bg: "bg-emerald-50", border: "border-emerald-300", text: "text-emerald-800", label: "Pali" },
  sanskrit: { bg: "bg-violet-50", border: "border-violet-300", text: "text-violet-800", label: "Sanskrit" },
};

function getStyle(lang: string) {
  return LANG_STYLES[lang.toLowerCase()] ?? {
    bg: "bg-slate-50", border: "border-slate-200", text: "text-slate-700", label: lang,
  };
}

export default function ClassificationResultPage() {
  const params = useParams();
  const router = useRouter();
  const { token } = useAuth();
  const [job, setJob] = useState<JobData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchJob = useCallback(async () => {
    try {
      const res = await axios.get(`/api/classification/jobs/${params.id}`);
      const data = res.data.data;
      setJob(data);
      if (data.status === "completed" || data.status === "failed") {
        setLoading(false);
      }
    } catch {
      toast.error("Failed to load job results");
      setLoading(false);
    }
  }, [params.id]);

  useEffect(() => {
    fetchJob();
  }, [fetchJob]);

  // WebSocket for live updates
  useEffect(() => {
    if (!token || !job || (job.status !== "queued" && job.status !== "processing")) return;
    const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/jobs/${job.id}?token=${token}`);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.status === "completed" || data.status === "failed") {
          fetchJob();
        } else {
          setJob((prev) => prev ? { ...prev, status: data.status } : prev);
        }
      } catch { /* ignore */ }
    };
    return () => ws.close();
  }, [token, job?.status, job?.id, fetchJob]);

  const statusConfig = {
    queued:     { icon: Clock,       color: "text-amber-500",  label: "Queued" },
    processing: { icon: Loader2,     color: "text-primary",    label: "Processing" },
    completed:  { icon: CheckCircle2, color: "text-emerald-500", label: "Completed" },
    failed:     { icon: XCircle,     color: "text-destructive", label: "Failed" },
  };

  if (loading && !job) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-3 text-muted-foreground">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm">Loading job results…</p>
      </div>
    );
  }

  if (!job) return null;

  const StatusIcon = statusConfig[job.status]?.icon ?? Clock;
  const statusColor = statusConfig[job.status]?.color ?? "text-muted-foreground";
  const statusLabel = statusConfig[job.status]?.label ?? job.status;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.push("/dashboard/classification")} className="gap-2 text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
        <div className="flex-1">
          <h1 className="text-xl font-bold tracking-tight">Classification Results</h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Strategy: <span className="font-medium capitalize">{job.segmentation_strategy}</span>
            {job.total_tokens > 0 && (
              <> · <span className="font-medium">{job.total_tokens}</span> tokens</>
            )}
          </p>
        </div>
        <div className={cn("flex items-center gap-1.5 text-sm font-medium", statusColor)}>
          <StatusIcon className={cn("h-4 w-4", job.status === "processing" && "animate-spin")} />
          {statusLabel}
        </div>
      </div>

      {/* Processing state */}
      {(job.status === "queued" || job.status === "processing") && (
        <div className="rounded-xl border border-primary/20 bg-primary/5 p-8 text-center space-y-3">
          <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
            <Zap className="h-6 w-6 text-primary" />
          </div>
          <p className="font-semibold text-sm">Processing your text…</p>
          <p className="text-xs text-muted-foreground">Real-time updates via WebSocket. This usually takes a few seconds.</p>
          <div className="w-48 h-1.5 bg-primary/20 rounded-full mx-auto overflow-hidden">
            <div className="h-full bg-primary rounded-full animate-pulse w-2/3" />
          </div>
        </div>
      )}

      {/* Failed state */}
      {job.status === "failed" && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-6 text-center space-y-2">
          <XCircle className="h-8 w-8 text-destructive mx-auto" />
          <p className="font-semibold text-sm">Classification failed</p>
          <p className="text-xs text-muted-foreground">An error occurred during processing.</p>
        </div>
      )}

      {/* Results */}
      {job.status === "completed" && job.segments && (
        <div className="space-y-4">
          {/* Legend */}
          <div className="flex flex-wrap gap-3">
            {Object.entries(LANG_STYLES).map(([lang, style]) => (
              <div key={lang} className={cn("flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium", style.bg, style.border, style.text)}>
                <span className={cn("h-1.5 w-1.5 rounded-full", style.text.replace("text", "bg"))} />
                {style.label}
              </div>
            ))}
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground ml-auto">
              <AlertTriangle className="h-3.5 w-3.5" />
              Click any segment to report an error
            </div>
          </div>

          {/* Segments */}
          <div className="rounded-xl border border-border bg-white shadow-sm p-6 leading-[2.2] text-base">
            {job.segments.map((seg) => (
              <SegmentFeedback key={seg.segment_index} segment={seg} token={token} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function SegmentFeedback({
  segment,
  token,
}: {
  segment: Segment;
  token: string | null;
}) {
  const [open, setOpen] = useState(false);
  const [correctedLang, setCorrectedLang] = useState<string | null>(null);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const style = getStyle(segment.predicted_language);

  const handleSubmit = async () => {
    if (!correctedLang) { toast.error("Please select a corrected language"); return; }
    setSubmitting(true);
    try {
      await axios.post("/api/annotations", {
        segment_id: segment.id,
        corrected_language: correctedLang,
        comment: comment || undefined,
      });
      toast.success("Correction submitted. Thank you!");
      setSubmitted(true);
      setOpen(false);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || error.response?.data?.error || "Failed to submit");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <Tooltip>
        <TooltipTrigger asChild>
          <PopoverTrigger asChild>
            <span
              className={cn(
                "inline cursor-pointer rounded-md border px-1.5 py-0.5 mx-0.5 transition-all hover:shadow-sm hover:opacity-80 select-none",
                style.bg, style.border, style.text,
                submitted && "opacity-50 cursor-default",
              )}
            >
              {segment.text}
            </span>
          </PopoverTrigger>
        </TooltipTrigger>
        <TooltipContent className="z-50 max-w-xs space-y-1">
          <div className="font-semibold">{style.label} ({(segment.confidence * 100).toFixed(1)}% confidence)</div>
          {segment.probabilities && (
            <div className="grid grid-cols-[1fr_auto] gap-x-3 gap-y-1 text-xs text-muted-foreground mt-1">
              {Object.entries(segment.probabilities)
                .sort(([, a], [, b]) => b - a)
                .map(([lang, prob]) => (
                  <div key={lang} className="contents">
                    <span className="capitalize">{lang}:</span>
                    <span className="font-mono">{(prob * 100).toFixed(2)}%</span>
                  </div>
              ))}
            </div>
          )}
          <div className="text-[10px] text-muted-foreground pt-1 border-t mt-2">Click to report misclassification</div>
        </TooltipContent>
      </Tooltip>
      <PopoverContent className="w-80 p-4" align="start" sideOffset={6}>
        {submitted ? (
          <div className="text-center py-3 space-y-2">
            <CheckCircle2 className="h-8 w-8 text-emerald-500 mx-auto" />
            <p className="font-semibold text-sm">Feedback submitted</p>
            <p className="text-xs text-muted-foreground">An admin will review your correction.</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <h4 className="font-semibold text-sm flex items-center gap-1.5 mb-1">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                Report Misclassification
              </h4>
              <p className="text-xs text-muted-foreground">
                Model predicted <strong className="capitalize">{segment.predicted_language}</strong>.
                Select the correct language below.
              </p>
            </div>

            <Select value={correctedLang} onValueChange={setCorrectedLang}>
              <SelectTrigger className="h-9 text-sm">
                <SelectValue placeholder="Select correct language…" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="sinhala">Sinhala</SelectItem>
                <SelectItem value="pali">Pali</SelectItem>
                <SelectItem value="sanskrit">Sanskrit</SelectItem>
              </SelectContent>
            </Select>

            <Textarea
              placeholder="Optional comment…"
              className="h-16 text-xs resize-none"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />

            <Button
              size="sm"
              className="w-full text-xs h-9"
              disabled={submitting || !correctedLang}
              onClick={handleSubmit}
            >
              {submitting ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" /> : null}
              Submit Correction
            </Button>
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}
