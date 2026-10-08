"use client";

import { useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { AlertTriangle, CheckCircle2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

export type Segment = {
  id: string;
  segment_index: number;
  text: string;
  predicted_language: string;
  confidence: number;
  probabilities?: Record<string, number>;
};

// Fallback until the model list loads; the three categories every model reports.
export const DEFAULT_CORRECTION_LANGUAGES = ["sinhala", "pali", "sanskrit"];

export const LANG_STYLES: Record<string, { bg: string; border: string; text: string; label: string }> = {
  sinhala:  { bg: "bg-blue-50",   border: "border-blue-300",  text: "text-blue-800",  label: "Sinhala" },
  pali:     { bg: "bg-emerald-50", border: "border-emerald-300", text: "text-emerald-800", label: "Pali" },
  sanskrit: { bg: "bg-violet-50", border: "border-violet-300", text: "text-violet-800", label: "Sanskrit" },
};

function getStyle(lang: string) {
  return LANG_STYLES[lang.toLowerCase()] ?? {
    bg: "bg-slate-50", border: "border-slate-200", text: "text-slate-700", label: lang,
  };
}

/** Merge newly received segments into a list, keyed and ordered by index. */
export function mergeSegments(current: Segment[], incoming: Segment[]): Segment[] {
  const byIndex = new Map(current.map((s) => [s.segment_index, s]));
  for (const s of incoming) byIndex.set(s.segment_index, s);
  return [...byIndex.values()].sort((a, b) => a.segment_index - b.segment_index);
}

export function LanguageLegend() {
  return (
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
  );
}

/** Classified text, highlighted by language, with runs of one language joined. */
export function SegmentText({
  segments,
  correctionLanguages,
}: {
  segments: Segment[];
  correctionLanguages: string[];
}) {
  return (
    <>
      {segments.map((seg, i, arr) => (
        <SegmentFeedback
          key={seg.segment_index}
          segment={seg}
          correctionLanguages={correctionLanguages}
          isFirstInGroup={i === 0 || arr[i - 1].predicted_language !== seg.predicted_language}
          isLastInGroup={i === arr.length - 1 || arr[i + 1].predicted_language !== seg.predicted_language}
        />
      ))}
    </>
  );
}

function SegmentFeedback({
  segment,
  correctionLanguages,
  isFirstInGroup = true,
  isLastInGroup = true,
}: {
  segment: Segment;
  correctionLanguages: string[];
  isFirstInGroup?: boolean;
  isLastInGroup?: boolean;
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
        <PopoverTrigger
          nativeButton={false}
          render={
            <TooltipTrigger
              render={
                <span
                  className={cn(
                    "inline cursor-pointer border-y transition-all hover:shadow-sm hover:opacity-80 select-none whitespace-pre-wrap",
                    style.bg, style.border, style.text,
                    isFirstInGroup ? "rounded-l-md pl-1.5 border-l ml-0.5" : "border-l-0 pl-0.5",
                    isLastInGroup ? "rounded-r-md pr-1.5 border-r mr-0.5" : "border-r-0 pr-0.5",
                    submitted && "opacity-50 cursor-default",
                  )}
                >
                  {segment.text}
                </span>
              }
            />
          }
        />
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
                {correctionLanguages.map((lang) => (
                  <SelectItem key={lang} value={lang} className="capitalize">
                    {lang}
                  </SelectItem>
                ))}
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
