"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Loader2, CheckCircle, XCircle } from "lucide-react";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";

type Annotation = {
  id: string;
  original_text: string;
  predicted_language: string;
  corrected_language: string;
  comment?: string;
  user_email: string;
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
    } catch (error) {
      toast.error("Failed to fetch annotations");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnnotations();
  }, []);

  const handleReview = async (id: string, isValid: boolean) => {
    try {
      setActionLoading(id);
      await axios.put(
        `/api/annotations/${id}/review`,
        { is_valid_for_training: isValid }
      );
      toast.success(isValid ? "Annotation approved for training" : "Annotation rejected");
      setAnnotations(annotations.filter((a) => a.id !== id));
    } catch (error) {
      toast.error("Failed to review annotation");
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Annotation Queue</h1>
        <p className="text-muted-foreground mt-2">
          Review user corrections. Approved corrections will be used to fine-tune the LangID models.
        </p>
      </div>

      <div className="bg-card border rounded-lg shadow-sm">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[30%]">Original Text</TableHead>
              <TableHead>Prediction</TableHead>
              <TableHead>User Correction</TableHead>
              <TableHead>Comment / User</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={5} className="h-32 text-center">
                  <Loader2 className="h-6 w-6 animate-spin mx-auto text-muted-foreground" />
                </TableCell>
              </TableRow>
            ) : annotations.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="h-32 text-center text-muted-foreground">
                  No pending annotations to review.
                </TableCell>
              </TableRow>
            ) : (
              annotations.map((annotation) => (
                <TableRow key={annotation.id}>
                  <TableCell className="font-medium text-sm leading-relaxed max-w-[300px] truncate" title={annotation.original_text}>
                    {annotation.original_text}
                  </TableCell>
                  <TableCell>
                    <span className="capitalize px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-semibold">
                      {annotation.predicted_language}
                    </span>
                  </TableCell>
                  <TableCell>
                    <span className="capitalize px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-semibold">
                      {annotation.corrected_language}
                    </span>
                  </TableCell>
                  <TableCell className="text-sm">
                    {annotation.comment ? (
                      <p className="italic mb-1">"{annotation.comment}"</p>
                    ) : null}
                    <span className="text-xs text-muted-foreground">{annotation.user_email}</span>
                  </TableCell>
                  <TableCell className="text-right space-x-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      className="border-red-200 text-red-700 hover:bg-red-50 hover:text-red-800"
                      disabled={actionLoading === annotation.id}
                      onClick={() => handleReview(annotation.id, false)}
                    >
                      {actionLoading === annotation.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <XCircle className="h-4 w-4 mr-1" />}
                      Reject
                    </Button>
                    <Button 
                      size="sm"
                      className="bg-green-600 hover:bg-green-700 text-white"
                      disabled={actionLoading === annotation.id}
                      onClick={() => handleReview(annotation.id, true)}
                    >
                      {actionLoading === annotation.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4 mr-1" />}
                      Approve
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
