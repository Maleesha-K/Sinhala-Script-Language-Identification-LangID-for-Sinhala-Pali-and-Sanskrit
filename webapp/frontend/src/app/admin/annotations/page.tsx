"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Loader2, CheckCircle, XCircle, Edit3, Inbox } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { cn } from "@/lib/utils";

type Annotation = {
  id: string;
  segment_id: string;
  user_id: string;
  original_language: string;
  corrected_language: string;
  comment?: string;
  created_at: string;
};

export default function AdminAnnotationsPage() {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchAnnotations = async () => {
    try {
      setLoading(true);
      const res = await axios.get("/api/annotations?pending_only=true");
      setAnnotations(res.data.data || []);
    } catch {
      toast.error("Failed to fetch annotations");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAnnotations(); }, []);

  const handleReview = async (id: string, isValid: boolean) => {
    try {
      setActionLoading(id);
      await axios.put(`/api/annotations/${id}/review`, { is_valid_for_training: isValid });
      toast.success(isValid ? "Annotation approved for training" : "Annotation rejected");
      setAnnotations((prev) => prev.filter((a) => a.id !== id));
    } catch {
      toast.error("Failed to review annotation");
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Annotation Review"
        description="Review user-submitted language corrections before they are used for model training."
      />

      <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/40 hover:bg-muted/40">
              <TableHead className="font-semibold">Predicted</TableHead>
              <TableHead className="font-semibold">Corrected To</TableHead>
              <TableHead className="font-semibold">Comment</TableHead>
              <TableHead className="font-semibold">Submitted</TableHead>
              <TableHead className="text-right font-semibold">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={5} className="h-36 text-center">
                  <Loader2 className="h-6 w-6 animate-spin mx-auto text-primary" />
                </TableCell>
              </TableRow>
            ) : annotations.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="h-36 text-center">
                  <div className="flex flex-col items-center gap-3 text-muted-foreground">
                    <Inbox className="h-8 w-8 opacity-40" />
                    <p className="text-sm">No pending annotations to review.</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              annotations.map((ann) => (
                <TableRow key={ann.id} className="hover:bg-muted/30">
                  <TableCell>
                    <span className={cn(
                      "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
                      "bg-destructive/10 text-destructive border border-destructive/20"
                    )}>
                      <XCircle className="h-3 w-3" />
                      <span className="capitalize">{ann.original_language}</span>
                    </span>
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
                  <TableCell className="text-sm text-muted-foreground max-w-[240px] truncate">
                    {ann.comment || <span className="italic opacity-50">No comment</span>}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {new Date(ann.created_at).toLocaleDateString(undefined, { dateStyle: "medium" })}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-8 gap-1.5 text-xs border-emerald-200 text-emerald-700 hover:bg-emerald-50"
                        disabled={actionLoading === ann.id}
                        onClick={() => handleReview(ann.id, true)}
                      >
                        {actionLoading === ann.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle className="h-3.5 w-3.5" />}
                        Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-8 gap-1.5 text-xs border-destructive/20 text-destructive hover:bg-destructive/5"
                        disabled={actionLoading === ann.id}
                        onClick={() => handleReview(ann.id, false)}
                      >
                        <XCircle className="h-3.5 w-3.5" />
                        Reject
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {annotations.length > 0 && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Edit3 className="h-3.5 w-3.5" />
          <span>{annotations.length} pending annotation{annotations.length !== 1 ? "s" : ""} awaiting review.</span>
        </div>
      )}
    </div>
  );
}
