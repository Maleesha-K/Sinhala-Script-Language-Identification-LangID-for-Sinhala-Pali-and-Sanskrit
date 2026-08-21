"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import axios from "axios";
import { toast } from "sonner";
import { ArrowLeft, Loader2, CheckCircle2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

type Segment = {
  segment_index: int;
  text: string;
  predicted_language: string;
  confidence: number;
};

type JobData = {
  id: string;
  status: "queued" | "processing" | "completed" | "failed";
  segmentation_strategy: string;
  total_tokens: number;
  segments?: Segment[];
};

export default function ClassificationResultPage() {
  const params = useParams();
  const router = useRouter();
  const [job, setJob] = useState<JobData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchJob = async () => {
      try {
        const res = await axios.get(`/api/classification/jobs/${params.id}`);
        setJob(res.data);
        
        // Poll if not finished
        if (res.data.status === "queued" || res.data.status === "processing") {
          setTimeout(fetchJob, 2000);
        } else {
          setLoading(false);
        }
      } catch (error) {
        toast.error("Failed to load job results");
        setLoading(false);
      }
    };

    fetchJob();
  }, [params.id]);

  if (loading && !job) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-muted-foreground">Loading job data...</p>
      </div>
    );
  }

  if (!job) return null;

  const getLanguageColor = (lang: string) => {
    switch (lang.toLowerCase()) {
      case "sinhala": return "bg-blue-100 text-blue-800 border-blue-200";
      case "pali": return "bg-green-100 text-green-800 border-green-200";
      case "sanskrit": return "bg-purple-100 text-purple-800 border-purple-200";
      default: return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Classification Results</h1>
          <div className="flex items-center gap-2 mt-2 text-sm text-muted-foreground">
            <span>Strategy: <span className="font-medium capitalize">{job.segmentation_strategy.replace("_", " ")}</span></span>
            <span>•</span>
            <span className="flex items-center gap-1">
              Status: 
              {job.status === "completed" && <CheckCircle2 className="h-4 w-4 text-green-500 inline" />}
              {job.status === "failed" && <XCircle className="h-4 w-4 text-red-500 inline" />}
              {(job.status === "queued" || job.status === "processing") && <Loader2 className="h-4 w-4 text-blue-500 animate-spin inline" />}
              <span className="font-medium capitalize">{job.status}</span>
            </span>
          </div>
        </div>
      </div>

      {(job.status === "queued" || job.status === "processing") && (
        <div className="bg-card border rounded-lg p-12 flex flex-col items-center justify-center text-center space-y-4 shadow-sm">
          <Loader2 className="h-10 w-10 animate-spin text-primary" />
          <div>
            <h3 className="text-lg font-semibold">Analyzing Text...</h3>
            <p className="text-muted-foreground mt-1">Our ML model is currently processing your request.</p>
          </div>
        </div>
      )}

      {job.status === "failed" && (
        <div className="bg-destructive/10 border-destructive/20 border rounded-lg p-6 text-center shadow-sm">
          <XCircle className="h-10 w-10 text-destructive mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-destructive">Processing Failed</h3>
          <p className="text-muted-foreground mt-1">An error occurred while analyzing the text.</p>
        </div>
      )}

      {job.status === "completed" && job.segments && (
        <div className="space-y-6">
          <div className="flex gap-4 mb-4 flex-wrap">
            <div className="px-3 py-1 rounded-full text-xs font-medium border bg-blue-100 text-blue-800 border-blue-200">Sinhala</div>
            <div className="px-3 py-1 rounded-full text-xs font-medium border bg-green-100 text-green-800 border-green-200">Pali</div>
            <div className="px-3 py-1 rounded-full text-xs font-medium border bg-purple-100 text-purple-800 border-purple-200">Sanskrit</div>
          </div>
          
          <div className="bg-card border rounded-lg p-6 shadow-sm leading-loose text-lg">
            {job.segments.map((segment) => (
              <span 
                key={segment.segment_index} 
                className={`inline-block px-1.5 py-0.5 m-0.5 rounded border transition-colors hover:shadow-md cursor-help ${getLanguageColor(segment.predicted_language)}`}
                title={`Confidence: ${(segment.confidence * 100).toFixed(1)}%`}
              >
                {segment.text}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
