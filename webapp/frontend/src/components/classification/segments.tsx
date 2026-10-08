"use client";

import { useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { AlertTriangle, CheckCircle2, Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { languageColor, languageLabel } from "@/lib/language-colors";

export type Segment = {
  id: string;
  segment_index: number;
  text: string;
  predicted_language: string;
  confidence: number;
  probabilities?: Record<string, number>;
  // Code-point offsets into the classified text (Python string indices).
  start_char_offset: number;
  end_char_offset: number;
};

// Fallback until the model list loads; the three categories every model reports.
export const DEFAULT_CORRECTION_LANGUAGES = ["sinhala", "pali", "sanskrit"];

// Below this confidence a sentence is underlined as uncertain.
export const LOW_CONFIDENCE = 0.5;

/** Merge newly received segments into a list, keyed and ordered by index. */
export function mergeSegments(current: Segment[], incoming: Segment[]): Segment[] {
  const byIndex = new Map(current.map((s) => [s.segment_index, s]));
  for (const s of incoming) byIndex.set(s.segment_index, s);
  return [...byIndex.values()].sort((a, b) => a.segment_index - b.segment_index);
}

export type LanguageShare = { language: string; chars: number; share: number };

/** Each language's share of the classified text, by characters, largest first. */
export function languageShares(segments: Segment[]): LanguageShare[] {
  const chars = new Map<string, number>();
  for (const s of segments) {
    const n = Array.from(s.text.trim()).length;
    chars.set(s.predicted_language, (chars.get(s.predicted_language) ?? 0) + n);
  }
  const total = [...chars.values()].reduce((a, b) => a + b, 0) || 1;
  return [...chars.entries()]
    .map(([language, n]) => ({ language, chars: n, share: n / total }))
    .sort((a, b) => b.chars - a.chars);
}

function percent(share: number): string {
  if (share > 0 && share < 0.01) return "<1%";
  return `${Math.round(share * 100)}%`;
}

/**
 * The languages found, as a distribution bar and a legend. Clicking a
 * language focuses it in the text (others fade); clicking again clears it.
 */
export function LanguageSummary({
  segments,
  focus,
  onFocus,
}: {
  segments: Segment[];
  focus: string | null;
  onFocus: (language: string | null) => void;
}) {
  const shares = languageShares(segments);
  const uncertain = segments.some((s) => s.confidence < LOW_CONFIDENCE);
  if (shares.length === 0) return null;
  return (
    <div className="space-y-3">
      <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-slate-100" aria-hidden>
        {shares.map(({ language, share }) => (
          <div
            key={language}
            className={cn(
              "h-full transition-opacity first:rounded-l-full last:rounded-r-full",
              languageColor(language).swatch,
              focus && focus !== language && "opacity-25",
            )}
            style={{ width: `${share * 100}%` }}
            title={`${languageLabel(language)} ${percent(share)}`}
          />
        ))}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {shares.map(({ language, share }) => {
          const color = languageColor(language);
          const active = focus === language;
          return (
            <button
              key={language}
              type="button"
              aria-pressed={active}
              onClick={() => onFocus(active ? null : language)}
              className={cn(
                "flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-all",
                color.chip,
                active && "ring-2 ring-offset-1 ring-current",
                focus && !active && "opacity-50 hover:opacity-100",
              )}
              title={active ? "Show all languages" : `Highlight ${languageLabel(language)} only`}
            >
              <span className={cn("h-2 w-2 rounded-full", color.swatch)} />
              {languageLabel(language)}
              <span className="tabular-nums opacity-70">{percent(share)}</span>
            </button>
          );
        })}
        {focus && (
          <button
            type="button"
            onClick={() => onFocus(null)}
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
          >
            <X className="h-3 w-3" /> Show all
          </button>
        )}
        <div className="ml-auto flex items-center gap-3 text-xs text-muted-foreground">
          {uncertain && (
            <span className="flex items-center gap-1.5">
              <span className="w-5 border-b-2 border-dashed border-slate-400" />
              Low confidence
            </span>
          )}
          <span className="flex items-center gap-1.5">
            <AlertTriangle className="h-3.5 w-3.5" />
            Click a sentence to report an error
          </span>
        </div>
      </div>
    </div>
  );
}

export type Piece =
  | { kind: "text"; text: string; pending?: boolean; language?: string }
  | { kind: "segment"; text: string; segment: Segment };

/**
 * Lays segments back onto the text they were cut from, so the result reads
 * exactly like the original: line breaks, blank lines and spacing between
 * sentences stay plain text, and only each sentence itself is highlighted.
 * Text not yet classified is returned as `pending` (when `running`) or plain.
 * Whitespace on one line between two sentences of the same language carries
 * that language, so a run of them reads as one highlight.
 *
 * Returns null when the offsets do not match the text (then callers fall back
 * to the segments alone).
 */
export function layoutSegments(text: string, segments: Segment[], running = false): Piece[] | null {
  // Offsets count code points (Python), not UTF-16 units.
  const chars = Array.from(text);
  const slice = (start: number, end?: number) => chars.slice(start, end).join("");
  const pieces: Piece[] = [];
  const plain = (t: string) => t && pieces.push({ kind: "text", text: t });
  let cursor = 0;

  for (const segment of [...segments].sort((a, b) => a.start_char_offset - b.start_char_offset)) {
    const { start_char_offset: start, end_char_offset: end } = segment;
    if (start < cursor || end > chars.length || slice(start, end) !== segment.text) return null;
    plain(slice(cursor, start));
    const [, lead, core, trail] = /^(\s*)([\s\S]*?)(\s*)$/.exec(segment.text)!;
    plain(lead);
    if (core) pieces.push({ kind: "segment", text: core, segment });
    plain(trail);
    cursor = end;
  }
  const rest = slice(cursor);
  if (rest) pieces.push({ kind: "text", text: rest, pending: running && rest.trim().length > 0 });

  // Join same-language sentences on one line into a single run.
  for (let i = 1; i < pieces.length - 1; i++) {
    const [before, gap, after] = [pieces[i - 1], pieces[i], pieces[i + 1]];
    if (
      gap.kind === "text" && !gap.pending && !gap.text.includes("\n") &&
      before.kind === "segment" && after.kind === "segment" &&
      before.segment.predicted_language === after.segment.predicted_language
    ) {
      pieces[i] = { ...gap, language: before.segment.predicted_language };
    }
  }
  return pieces;
}

/** Classified text, highlighted by language, laid out exactly as the original. */
export function SegmentText({
  text,
  segments,
  correctionLanguages,
  running = false,
  focus = null,
}: {
  /** The classified text; segments index into it. */
  text: string | null | undefined;
  segments: Segment[];
  correctionLanguages: string[];
  /** Still classifying: unclassified text is shown as pending. */
  running?: boolean;
  /** Highlight only this language; the rest fades. */
  focus?: string | null;
}) {
  const pieces = (text != null && layoutSegments(text, segments, running)) || segments.map(
    (segment): Piece => ({ kind: "segment", text: segment.text, segment }),
  );
  return (
    <div className="whitespace-pre-wrap break-words">
      {pieces.map((piece, i) =>
        piece.kind === "segment" ? (
          <SegmentFeedback
            key={i}
            segment={piece.segment}
            correctionLanguages={correctionLanguages}
            dimmed={!!focus && piece.segment.predicted_language !== focus}
          >
            {piece.text}
          </SegmentFeedback>
        ) : (
          <span
            key={i}
            className={cn(
              piece.pending && "text-slate-400",
              piece.language && (focus && piece.language !== focus ? "opacity-30" : languageColor(piece.language).mark),
            )}
          >
            {piece.text}
          </span>
        ),
      )}
    </div>
  );
}

function SegmentFeedback({
  segment,
  correctionLanguages,
  dimmed = false,
  children,
}: {
  segment: Segment;
  correctionLanguages: string[];
  /** Another language is focused. */
  dimmed?: boolean;
  /** The sentence as it appears in the text (without surrounding whitespace). */
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const [correctedLang, setCorrectedLang] = useState<string | null>(null);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const color = languageColor(segment.predicted_language);
  const label = languageLabel(segment.predicted_language);
  const uncertain = segment.confidence < LOW_CONFIDENCE;

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
                    "cursor-pointer rounded box-decoration-clone transition-all hover:brightness-95",
                    dimmed ? "opacity-30" : [color.mark, color.text],
                    uncertain && "underline decoration-dashed decoration-1 underline-offset-4",
                    submitted && "opacity-50 cursor-default",
                  )}
                >
                  {children}
                </span>
              }
            />
          }
        />
        <TooltipContent className="z-50 max-w-none">
          <div className="w-60 space-y-2 py-0.5">
            <div className="flex items-center gap-2 font-semibold">
              <span className={cn("h-2 w-2 rounded-full", color.swatch)} />
              {label}
              <span className="ml-auto font-normal tabular-nums opacity-80">{(segment.confidence * 100).toFixed(1)}%</span>
            </div>
            {uncertain && <div className="text-[11px] text-amber-300">Low confidence: the model is unsure.</div>}
            {segment.probabilities && (
              <div className="space-y-1.5">
                {Object.entries(segment.probabilities)
                  .sort(([, a], [, b]) => b - a)
                  .map(([lang, prob]) => (
                    <div key={lang} className="grid grid-cols-[5.5rem_1fr_3rem] items-center gap-2 text-[11px]">
                      <span className="truncate opacity-80">{languageLabel(lang)}</span>
                      <span className="h-1.5 rounded-full bg-white/15 overflow-hidden">
                        <span className={cn("block h-full rounded-full", languageColor(lang).swatch)} style={{ width: `${prob * 100}%` }} />
                      </span>
                      <span className="text-right font-mono tabular-nums opacity-80">{(prob * 100).toFixed(1)}%</span>
                    </div>
                ))}
              </div>
            )}
            <div className="text-[10px] opacity-60 pt-1.5 border-t border-white/15">Click to report a misclassification</div>
          </div>
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
                Model predicted <strong>{label}</strong>.
                Select the correct language below.
              </p>
            </div>

            <Select value={correctedLang} onValueChange={setCorrectedLang}>
              <SelectTrigger className="h-9 text-sm">
                <SelectValue placeholder="Select correct language…">
                  {(value: string | null) => (value ? languageLabel(value) : "Select correct language…")}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                {correctionLanguages.map((lang) => (
                  <SelectItem key={lang} value={lang}>
                    {languageLabel(lang)}
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
