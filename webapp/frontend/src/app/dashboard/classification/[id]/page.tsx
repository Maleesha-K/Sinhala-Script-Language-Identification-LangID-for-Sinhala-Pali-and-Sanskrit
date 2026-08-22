"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import axios from "axios";
import { toast } from "sonner";
import { ArrowLeft, Loader2, CheckCircle2, XCircle, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useAuth } from "@/store/useAuth";

type Segment = {
  id: string;
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
  const { token } = useAuth();
  const [job, setJob] = useState<JobData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchJob = async () => {
    try {
      const res = await axios.get(`http://localhost:8000/api/v1/classification/jobs/${params.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setJob(res.data.data);
      if (res.data.data.status === "completed" || res.data.data.status === "failed") {
        setLoading(false);
      }
    } catch (error) {
      toast.error("Failed to load job results");
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) fetchJob();
  }, [token, params.id]);

  useEffect(() => {
    if (!token || !job || (job.status !== "queued" && job.status !== "processing")) return;
    
    // Connect to WebSocket using the token as query parameter
    const wsUrl = `ws://localhost:8000/api/v1/ws/jobs/${job.id}?token=${token}`;
    const ws = new WebSocket(wsUrl);
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.status === "completed" || data.status === "failed") {
          fetchJob();
        } else {
          setJob(prev => prev ? { ...prev, status: data.status } : prev);
        }
      } catch (err) {
        console.error("WebSocket message parsing error", err);
      }
    };
    
    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
    };

    return () => {
      ws.close();
    };
  }, [token, job?.status, job?.id]);

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
              <SegmentFeedback key={segment.segment_index} segment={segment} getLanguageColor={getLanguageColor} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Subcomponent to handle individual segment feedback state
function SegmentFeedback({ segment, getLanguageColor }: { segment: Segment, getLanguageColor: (l: string) => string }) {
  const { token } = useAuth();
  const [open, setOpen] = useState(false);
  const [correctedLang, setCorrectedLang] = useState("");
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async () => {
    if (!correctedLang) {
      toast.error("Please select a corrected language");
      return;
    }
    setSubmitting(true);
    try {
      await axios.post("/api/v1/annotations", {
        segment_id: segment.id,
        corrected_language: correctedLang,
        comment: comment
      }, {
        baseURL: "http://localhost:8000",
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Thank you for your feedback!");
      setSubmitted(true);
      setOpen(false);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to submit feedback");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <span 
          className={`inline-block px-1.5 py-0.5 m-0.5 rounded border transition-colors hover:shadow-md cursor-pointer hover:opacity-80 ${getLanguageColor(segment.predicted_language)}`}
          title={`Confidence: ${(segment.confidence * 100).toFixed(1)}% - Click to report error`}
        >
          {segment.text}
        </span>
      </PopoverTrigger>
      <PopoverContent className="w-80 p-4" align="start">
        {submitted ? (
          <div className="text-center py-4 space-y-2">
            <CheckCircle2 className="h-8 w-8 text-green-500 mx-auto" />
            <p className="font-medium text-sm">Feedback received.</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="space-y-1">
              <h4 className="font-semibold text-sm flex items-center gap-1.5">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                Report Misclassification
              </h4>
              <p className="text-xs text-muted-foreground">
                Model predicted <strong className="capitalize">{segment.predicted_language}</strong>. If this is incorrect, let us know.
              </p>
            </div>
            
            <div className="space-y-2">
              <Select value={correctedLang} onValueChange={setCorrectedLang}>
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue placeholder="Correct language..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="sinhala">Sinhala</SelectItem>
                  <SelectItem value="pali">Pali</SelectItem>
                  <SelectItem value="sanskrit">Sanskrit</SelectItem>
                </SelectContent>
              </Select>
              
              <Textarea 
                placeholder="Optional comment..." 
                className="h-16 text-xs resize-none"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
              />
            </div>
            
            <Button size="sm" className="w-full text-xs h-8" disabled={submitting} onClick={handleSubmit}>
              {submitting ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : null}
              Submit Correction
            </Button>
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}
