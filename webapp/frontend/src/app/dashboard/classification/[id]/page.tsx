"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import axios from "axios";
import { toast } from "sonner";
import { ArrowLeft, Loader2, CheckCircle2, XCircle, Clock, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/auth-context";
import { apiErrorDetail, cn } from "@/lib/utils";
import { useLiveChannel, type LiveEvent } from "@/lib/live";
import {
  DEFAULT_CORRECTION_LANGUAGES, LanguageLegend, SegmentText, mergeSegments, type Segment,
} from "@/components/classification/segments";

type JobStatus = "queued" | "processing" | "completed" | "failed";

type JobData = {
  id: string;
  status: JobStatus;
  model_name?: string;
  segmentation_strategy: string;
  total_tokens: number;
  error_message?: string | null;
  done?: number | null;
  total?: number | null;
  segments: Segment[];
};

export default function ClassificationResultPage() {
  const params = useParams();
  const router = useRouter();
  const { refreshUser } = useAuth();
  const [job, setJob] = useState<JobData | null>(null);
  const [correctionLanguages, setCorrectionLanguages] = useState<string[]>(DEFAULT_CORRECTION_LANGUAGES);
  const [modelLabel, setModelLabel] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchJob = useCallback(async () => {
    try {
      const res = await axios.get(`/api/classification/jobs/${params.id}`);
      const data = res.data.data;
      setJob({ ...data, segments: data.segments ?? [] });
    } catch (error) {
      toast.error(apiErrorDetail(error, "Failed to load job results"));
    } finally {
      setLoading(false);
    }
  }, [params.id]);

  // Load once; while the job runs, the live channel reloads and streams.
  useEffect(() => {
    fetchJob();
  }, [fetchJob]);

  const isRunning = job?.status === "queued" || job?.status === "processing";

  useLiveChannel({
    path: `/ws/jobs/${params.id}`,
    enabled: isRunning,
    load: fetchJob,
    onEvent: (event: LiveEvent) => {
      setJob((prev) => {
        if (!prev) return prev;
        if (event.type === "segments") {
          return {
            ...prev,
            segments: mergeSegments(prev.segments, event.segments as Segment[]),
            done: event.done as number,
            total: event.total as number,
          };
        }
        if (event.type === "status") {
          return {
            ...prev,
            status: event.status as JobStatus,
            done: (event.done as number | undefined) ?? prev.done,
            total: (event.total as number | undefined) ?? prev.total,
            error_message: event.status === "failed" ? (event.message as string) || prev.error_message : prev.error_message,
          };
        }
        return prev;
      });
    },
    isFinal: (event) => event.type === "status" && (event.status === "completed" || event.status === "failed"),
  });

  // The job is charged when it starts, so refresh the balance in the header.
  useEffect(() => {
    if (job?.status === "processing" || job?.status === "completed") refreshUser();
  }, [job?.status, refreshUser]);

  // The correction options depend on the model that produced this job: the
  // baseline is three-way, the fine-tuned checkpoints also know the replay
  // languages.
  useEffect(() => {
    if (!job?.model_name) return;
    let cancelled = false;
    axios
      .get("/api/classification/models")
      .then((res) => {
        if (cancelled) return;
        const match = (res.data?.data ?? []).find((m: { id: string }) => m.id === job.model_name);
        if (match?.label) setModelLabel(match.label);
        if (match?.correction_languages?.length) {
          setCorrectionLanguages(match.correction_languages);
        }
      })
      .catch(() => {
        /* keep the three-category default */
      });
    return () => {
      cancelled = true;
    };
  }, [job?.model_name]);

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
            Model: <span className="font-medium">{modelLabel ?? job.model_name ?? "—"}</span>
            {" · "}Strategy: <span className="font-medium capitalize">{job.segmentation_strategy}</span>
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

      {/* Progress, while segments stream in below */}
      {isRunning && (
        <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Zap className="h-4 w-4 text-primary" />
            {job.status === "queued"
              ? "Waiting for a worker…"
              : job.total
                ? `Classified ${job.done ?? 0} of ${job.total} segments`
                : "Segmenting…"}
          </div>
          <div className="h-1.5 bg-primary/20 rounded-full overflow-hidden">
            {job.total ? (
              <div
                className="h-full bg-primary rounded-full transition-all"
                style={{ width: `${Math.round(100 * (job.done ?? 0) / job.total)}%` }}
              />
            ) : (
              <div className="h-full bg-primary rounded-full animate-pulse w-1/3" />
            )}
          </div>
        </div>
      )}

      {/* Failed state */}
      {job.status === "failed" && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-6 text-center space-y-2">
          <XCircle className="h-8 w-8 text-destructive mx-auto" />
          <p className="font-semibold text-sm">Classification failed</p>
          <p className="text-xs text-muted-foreground">{job.error_message || "An error occurred during processing."}</p>
          {job.segments.length > 0 && (
            <p className="text-xs text-muted-foreground">The segments classified before the failure are shown below. You were not charged.</p>
          )}
        </div>
      )}

      {/* Results, as they arrive */}
      {job.segments.length > 0 && (
        <div className="space-y-4">
          <LanguageLegend />
          <div className="rounded-xl border border-border bg-white shadow-sm p-6 leading-[2.2] text-base">
            <SegmentText segments={job.segments} correctionLanguages={correctionLanguages} />
          </div>
        </div>
      )}
    </div>
  );
}
