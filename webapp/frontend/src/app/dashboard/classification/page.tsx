"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { toast } from "sonner";
import { Loader2, Activity, MessageSquare, AlignLeft, FileText, Wand2, Cpu, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { PageHeader } from "@/components/layout/page-header";
import { cn } from "@/lib/utils";

type Strategy = "sentence" | "paragraph" | "full_text" | "auto";

type ModelInfo = {
  id: string;
  label: string;
  description: string;
  family: string;
  is_baseline: boolean;
  available: boolean;
};

const BASELINE_MODEL = "sklearn_langid";

const strategies: { value: Strategy; icon: React.ElementType; label: string; desc: string }[] = [
  { value: "auto", icon: Wand2, label: "Auto", desc: "Smart split by newlines, punctuation, and special characters." },
  { value: "sentence", icon: MessageSquare, label: "Sentence", desc: "Split by punctuation marks. Best for mixed-language texts." },
  { value: "paragraph", icon: AlignLeft, label: "Paragraph", desc: "Split by newlines. Best for prose with clear paragraph breaks." },
  { value: "full_text", icon: FileText, label: "Full Text", desc: "Treat entire text as one block. Best for short passages." },
];

export default function ClassificationPage() {
  const router = useRouter();
  const [text, setText] = useState("");
  const [strategy, setStrategy] = useState<Strategy>("sentence");
  const [loading, setLoading] = useState(false);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [modelName, setModelName] = useState<string>(BASELINE_MODEL);
  const [modelsLoading, setModelsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    axios
      .get("/api/classification/models")
      .then((res) => {
        if (cancelled) return;
        const list: ModelInfo[] = res.data?.data ?? [];
        setModels(list);
        // Keep the baseline selected unless it is somehow unavailable.
        const preferred = list.find((m) => m.id === BASELINE_MODEL && m.available) ?? list.find((m) => m.available);
        if (preferred) setModelName(preferred.id);
      })
      .catch(() => {
        if (!cancelled) toast.error("Could not load the model list; using the baseline.");
      })
      .finally(() => {
        if (!cancelled) setModelsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) {
      toast.error("Please enter some text to classify");
      return;
    }

    setLoading(true);
    try {
      const res = await axios.post("/api/classification/jobs", {
        input_text: text,
        segmentation_strategy: strategy,
        model_name: modelName,
      });
      toast.success("Classification job started!");
      router.push(`/dashboard/classification/${res.data.data.id}`);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to start classification");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl space-y-6">
      <PageHeader
        title="Language Identification"
        description="Paste Sinhala, Pali, or Sanskrit text to classify it. Choose a segmentation strategy to control how the text is split."
      />

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Text input */}
        <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-border bg-muted/40">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Input Text</p>
          </div>
          <Textarea
            id="text-input"
            placeholder="ශ්‍රී ලංකාවේ ඉතිහාසය... / बुद्धं शरणं गच्छामि..."
            className="min-h-[220px] resize-y border-0 rounded-none text-sm focus-visible:ring-0 focus-visible:ring-offset-0 p-4"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <div className="px-4 py-2 border-t border-border bg-muted/40 flex justify-end">
            <span className="text-xs text-muted-foreground">{text.length} characters</span>
          </div>
        </div>

        {/* Model selection */}
        <div className="space-y-3">
          <div className="flex items-baseline justify-between">
            <p className="text-sm font-semibold text-foreground">Model</p>
            {modelsLoading && <span className="text-xs text-muted-foreground">Loading models…</span>}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {models.map((m) => {
              const Icon = m.is_baseline ? Cpu : Sparkles;
              const selected = modelName === m.id;
              return (
                <button
                  key={m.id}
                  type="button"
                  disabled={!m.available}
                  onClick={() => setModelName(m.id)}
                  title={m.available ? m.description : "Checkpoint not found on this machine"}
                  className={cn(
                    "text-left rounded-xl border-2 p-4 transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                    !m.available && "opacity-50 cursor-not-allowed",
                    selected
                      ? "border-primary bg-primary/5 shadow-sm"
                      : "border-border bg-white hover:border-primary/40 hover:bg-secondary/50"
                  )}
                >
                  <div className="flex items-center gap-2 mb-3">
                    <div className={cn(
                      "h-8 w-8 rounded-lg flex items-center justify-center transition-colors",
                      selected ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                    )}>
                      <Icon className="h-4 w-4" />
                    </div>
                    {m.is_baseline && (
                      <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground bg-muted px-2 py-0.5 rounded">
                        Baseline
                      </span>
                    )}
                  </div>
                  <p className={cn("text-sm font-semibold mb-1", selected ? "text-primary" : "text-foreground")}>
                    {m.label}
                  </p>
                  <p className="text-xs text-muted-foreground leading-relaxed">{m.description}</p>
                  {!m.available && (
                    <p className="text-xs text-destructive mt-2">Checkpoint not found</p>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Strategy selection */}
        <div className="space-y-3">
          <p className="text-sm font-semibold text-foreground">Segmentation Strategy</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {strategies.map(({ value, icon: Icon, label, desc }) => (
              <button
                key={value}
                type="button"
                onClick={() => setStrategy(value)}
                className={cn(
                  "text-left rounded-xl border-2 p-4 transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                  strategy === value
                    ? "border-primary bg-primary/5 shadow-sm"
                    : "border-border bg-white hover:border-primary/40 hover:bg-secondary/50"
                )}
              >
                <div className={cn(
                  "h-8 w-8 rounded-lg flex items-center justify-center mb-3 transition-colors",
                  strategy === value ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                )}>
                  <Icon className="h-4 w-4" />
                </div>
                <p className={cn("text-sm font-semibold mb-1", strategy === value ? "text-primary" : "text-foreground")}>
                  {label}
                </p>
                <p className="text-xs text-muted-foreground leading-relaxed">{desc}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Submit */}
        <div className="flex justify-end">
          <Button type="submit" size="lg" disabled={loading} className="gap-2 shadow-sm">
            {loading ? (
              <><Loader2 className="h-4 w-4 animate-spin" />Processing…</>
            ) : (
              <><Activity className="h-4 w-4" />Identify Language</>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
