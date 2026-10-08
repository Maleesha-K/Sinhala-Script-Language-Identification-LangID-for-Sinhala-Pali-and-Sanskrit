"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { Loader2, UploadCloud, ScanText, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import type { OCREngine } from "@/lib/ocr-engines";

import { buttonVariants } from "@/components/ui/button";

type ModelInfo = { id: string; label: string; is_baseline: boolean; available: boolean };

// Select value for "do not classify the pages".
const OCR_ONLY = "none";

export function UploadModal({ onUploadSuccess }: { onUploadSuccess: (document: { id: string }) => void }) {
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [engines, setEngines] = useState<OCREngine[]>([]);
  const [engineId, setEngineId] = useState<string>("tesseract");
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [modelId, setModelId] = useState<string>(OCR_ONLY);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    axios
      .get("/api/documents/ocr-engines")
      .then((res) => {
        if (cancelled) return;
        const list: OCREngine[] = Array.isArray(res.data?.data) ? res.data.data : Array.isArray(res.data) ? res.data : [];
        setEngines(list);
        const preferred = list.find((e) => e.is_default) ?? list[0];
        if (preferred) setEngineId((current) => (list.some((e) => e.id === current) ? current : preferred.id));
      })
      .catch(() => {
        if (!cancelled) toast.error("Could not load OCR engines; using Tesseract.");
      });
    return () => {
      cancelled = true;
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    axios
      .get("/api/classification/models")
      .then((res) => {
        if (cancelled) return;
        const list: ModelInfo[] = (res.data?.data ?? []).filter((m: ModelInfo) => m.available);
        setModels(list);
        // Classify with the baseline unless the user picked something else.
        setModelId((current) =>
          current !== OCR_ONLY && list.some((m) => m.id === current)
            ? current
            : (list.find((m) => m.is_baseline) ?? list[0])?.id ?? OCR_ONLY,
        );
      })
      .catch(() => {
        /* OCR only */
      });
    return () => {
      cancelled = true;
    };
  }, [open]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.type !== "application/pdf") {
        toast.error("Only PDF files are supported");
        setFile(null);
        return;
      }
      setFile(selectedFile);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("ocr_engine", engineId);
    if (modelId !== OCR_ONLY) formData.append("lid_model", modelId);

    try {
      const res = await fetch("/api/documents", {
        method: "POST",
        body: formData,
      });
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Upload failed");
      }
      const created = await res.json();

      toast.success("Document uploaded successfully");
      setOpen(false);
      setFile(null);
      onUploadSuccess(created);
    } catch (error: any) {
      toast.error(error.message || "Failed to upload document");
    } finally {
      setUploading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger className={buttonVariants({ variant: "default" })}>
        <UploadCloud className="mr-2 h-4 w-4" />
        Upload Document
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Upload Document</DialogTitle>
          <DialogDescription>
            Upload a PDF document to begin language identification and processing.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleUpload} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="file">PDF File</Label>
            <Input 
              id="file" 
              type="file" 
              accept=".pdf" 
              onChange={handleFileChange}
              required 
            />
          </div>
          {engines.length > 0 && (
            <div className="space-y-2">
              <Label>OCR Engine</Label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {engines.map((engine) => {
                  const selected = engineId === engine.id;
                  const Icon = engine.is_default ? ScanText : Sparkles;
                  return (
                    <button
                      key={engine.id}
                      type="button"
                      onClick={() => setEngineId(engine.id)}
                      className={cn(
                        "text-left rounded-lg border-2 p-3 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                        selected
                          ? "border-primary bg-primary/5"
                          : "border-border hover:border-primary/40 hover:bg-secondary/50"
                      )}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <Icon className={cn("h-4 w-4", selected ? "text-primary" : "text-muted-foreground")} />
                        <span className={cn("text-sm font-semibold", selected && "text-primary")}>{engine.label}</span>
                      </div>
                      <p className="text-xs text-muted-foreground leading-snug">{engine.description}</p>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
          <div className="space-y-2">
            <Label>Language identification</Label>
            <Select value={modelId} onValueChange={(value) => setModelId(value ?? OCR_ONLY)}>
              <SelectTrigger className="w-full">
                <SelectValue>
                  {(value: string) =>
                    value === OCR_ONLY ? "OCR only" : models.find((m) => m.id === value)?.label ?? value
                  }
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                {models.map((m) => (
                  <SelectItem key={m.id} value={m.id}>{m.label}</SelectItem>
                ))}
                <SelectItem value={OCR_ONLY}>OCR only</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground leading-snug">
              Each page is classified as soon as its text is read, so results appear page by page.
            </p>
          </div>
          <Button type="submit" className="w-full" disabled={uploading || !file}>
            {uploading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Upload & Process
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
