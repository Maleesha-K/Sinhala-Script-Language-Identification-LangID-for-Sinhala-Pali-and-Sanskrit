"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import {
  Loader2, Download, Trash2, FileText, CheckCircle2, Clock, XCircle, Upload, Eye,
} from "lucide-react";
import { UploadModal } from "@/components/documents/upload-modal";
import { PageHeader } from "@/components/layout/page-header";
import { cn } from "@/lib/utils";

type DocumentStatus = "uploading" | "ready" | "deleted";

type Document = {
  id: string;
  filename: string;
  upload_status: DocumentStatus;
  size_bytes: number;
  created_at: string;
};

const statusConfig: Record<DocumentStatus, { icon: React.ElementType; label: string; className: string }> = {
  uploading: { icon: Loader2,      label: "Processing", className: "text-primary" },
  ready:     { icon: CheckCircle2, label: "Ready",      className: "text-emerald-600" },
  deleted:   { icon: XCircle,      label: "Deleted",    className: "text-destructive" },
};

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);

  const router = useRouter();

  const fetchDocuments = async () => {
    try {
      const res = await axios.get("/api/documents");
      setDocuments(res.data);
    } catch {
      toast.error("Failed to load documents");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
    const interval = setInterval(fetchDocuments, 6000);
    return () => clearInterval(interval);
  }, []);

  const handleDownload = async (e: React.MouseEvent, docId: string, filename: string) => {
    e.stopPropagation();
    try {
      const res = await axios.get(`/api/documents/${docId}/download`);
      const { download_url } = res.data;
      const a = document.createElement("a");
      a.href = download_url;
      a.setAttribute("download", filename);
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch {
      toast.error("Failed to download document");
    }
  };

  const handleDelete = async (e: React.MouseEvent, docId: string) => {
    e.stopPropagation();
    if (!confirm("Delete this document? This action cannot be undone.")) return;
    try {
      await axios.delete(`/api/documents/${docId}`);
      toast.success("Document deleted");
      fetchDocuments();
    } catch {
      toast.error("Failed to delete document");
    }
  };

  const handleRowClick = (docId: string, status: DocumentStatus) => {
    if (status === "ready") {
      router.push(`/dashboard/documents/${docId}`);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Documents"
        description="Upload PDFs to extract text and run language identification."
        actions={<UploadModal onUploadSuccess={fetchDocuments} />}
      />

      <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/40 hover:bg-muted/40">
              <TableHead className="font-semibold">Filename</TableHead>
              <TableHead className="font-semibold">Status</TableHead>
              <TableHead className="font-semibold">Size</TableHead>
              <TableHead className="font-semibold">Uploaded</TableHead>
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
            ) : documents.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="h-36 text-center">
                  <div className="flex flex-col items-center gap-3 text-muted-foreground">
                    <Upload className="h-8 w-8 opacity-40" />
                    <p className="text-sm">No documents yet. Upload a PDF to get started.</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              documents.map((doc) => {
                const status = statusConfig[doc.upload_status];
                const StatusIcon = status.icon;
                return (
                  <TableRow 
                    key={doc.id} 
                    className={cn("hover:bg-muted/30 transition-colors", doc.upload_status === "ready" && "cursor-pointer")}
                    onClick={() => handleRowClick(doc.id, doc.upload_status)}
                  >
                    <TableCell>
                      <div className="flex items-center gap-2.5">
                        <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                        <span className="text-sm font-medium truncate max-w-[240px]">{doc.filename}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className={cn("flex items-center gap-1.5 text-sm font-medium", status.className)}>
                        <StatusIcon className={cn("h-4 w-4", doc.upload_status === "uploading" && "animate-spin")} />
                        {status.label}
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {(doc.size_bytes / 1024 / 1024).toFixed(2)} MB
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {new Date(doc.created_at).toLocaleDateString(undefined, { dateStyle: "medium" })}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          disabled={doc.upload_status !== "ready"}
                          onClick={(e) => {
                            e.stopPropagation();
                            router.push(`/dashboard/documents/${doc.id}`);
                          }}
                          className="h-8 w-8 text-muted-foreground hover:text-primary hover:bg-primary/10"
                          title="View OCR Results"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          disabled={doc.upload_status !== "ready"}
                          onClick={(e) => handleDownload(e, doc.id, doc.filename)}
                          className="h-8 w-8 text-muted-foreground hover:text-primary hover:bg-primary/10"
                          title="Download"
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                          onClick={(e) => handleDelete(e, doc.id)}
                          title="Delete"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
