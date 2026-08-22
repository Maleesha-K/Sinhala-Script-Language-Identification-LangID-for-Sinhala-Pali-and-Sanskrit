"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import axios from "axios";
import { toast } from "sonner";
import {
  Loader2, ArrowLeft, Languages, FileText, Download,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/layout/page-header";
import { cn } from "@/lib/utils";

type Document = {
  id: string;
  filename: string;
  upload_status: string;
  size_bytes: number;
  created_at: string;
};

type DocumentPage = {
  id: string;
  page_number: number;
  extracted_text: string | null;
  extraction_method: string | null;
  status: string;
};

export default function DocumentDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const documentId = params.id as string;

  const [document, setDocument] = useState<Document | null>(null);
  const [pages, setPages] = useState<DocumentPage[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [activeTab, setActiveTab] = useState<number>(1);

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        const [docRes, pagesRes] = await Promise.all([
          axios.get(`/api/documents/${documentId}`),
          axios.get(`/api/documents/${documentId}/pages`)
        ]);
        setDocument(docRes.data);
        setPages(pagesRes.data);
        
        if (pagesRes.data.length > 0) {
          setActiveTab(pagesRes.data[0].page_number);
        }
      } catch (err) {
        toast.error("Failed to load document details");
        router.push("/dashboard/documents");
      } finally {
        setLoading(false);
      }
    };
    
    if (documentId) {
      fetchDetails();
    }
  }, [documentId, router]);

  const handleIdentifyLanguage = async () => {
    // Combine text from all pages
    const fullText = pages
      .map(p => p.extracted_text || "")
      .filter(t => t.trim().length > 0)
      .join("\n\n");
      
    if (!fullText) {
      toast.error("No text found in this document to analyze.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await axios.post("/api/classification/jobs", {
        input_text: fullText,
        segmentation_strategy: "sentence" // Default strategy
      });
      
      toast.success("Classification job created!");
      router.push(`/dashboard/classification/${res.data.data.id}`);
    } catch (err) {
      toast.error("Failed to start language identification");
      setSubmitting(false);
    }
  };

  const handleDownload = async () => {
    if (!document) return;
    try {
      const res = await axios.get(`/api/documents/${document.id}/download`);
      const { download_url } = res.data;
      const a = window.document.createElement("a");
      a.href = download_url;
      a.setAttribute("download", document.filename);
      window.document.body.appendChild(a);
      a.click();
      window.document.body.removeChild(a);
    } catch {
      toast.error("Failed to download document");
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-muted-foreground text-sm font-medium">Loading document details...</p>
      </div>
    );
  }

  if (!document) return null;

  const activePage = pages.find(p => p.page_number === activeTab);
  const totalExtractedChars = pages.reduce((acc, p) => acc + (p.extracted_text?.length || 0), 0);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-4 mb-2">
        <Button 
          variant="ghost" 
          size="sm" 
          className="text-muted-foreground hover:text-foreground -ml-2"
          onClick={() => router.push("/dashboard/documents")}
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Documents
        </Button>
      </div>

      <PageHeader
        title={document.filename}
        description={`Uploaded on ${new Date(document.created_at).toLocaleDateString()} • ${(document.size_bytes / 1024 / 1024).toFixed(2)} MB • ${pages.length} Pages`}
        actions={
          <div className="flex items-center gap-3">
            <Button variant="outline" onClick={handleDownload} className="gap-2">
              <Download className="h-4 w-4" />
              Download Original
            </Button>
            <Button 
              onClick={handleIdentifyLanguage} 
              disabled={submitting || pages.length === 0} 
              className="gap-2 bg-emerald-600 hover:bg-emerald-700"
            >
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Languages className="h-4 w-4" />}
              Identify Language
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Left sidebar: Page Navigation */}
        <div className="md:col-span-3 space-y-4">
          <div className="bg-white rounded-xl border border-border overflow-hidden p-4 shadow-sm">
            <h3 className="font-semibold text-sm mb-3 text-slate-800">Document Pages</h3>
            <div className="space-y-1.5 max-h-[500px] overflow-y-auto pr-1 custom-scrollbar">
              {pages.map((page) => (
                <button
                  key={page.id}
                  onClick={() => setActiveTab(page.page_number)}
                  className={cn(
                    "w-full flex items-center justify-between px-3 py-2 text-sm rounded-lg transition-colors",
                    activeTab === page.page_number 
                      ? "bg-primary/10 text-primary font-medium" 
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  )}
                >
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 shrink-0" />
                    <span>Page {page.page_number}</span>
                  </div>
                  {page.status === "completed" && (
                    <span className="text-xs bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded-full font-medium">
                      {(page.extracted_text?.length || 0)} chars
                    </span>
                  )}
                  {page.status === "failed" && (
                    <span className="text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded-full font-medium">
                      Failed
                    </span>
                  )}
                </button>
              ))}
              {pages.length === 0 && (
                <div className="text-sm text-muted-foreground text-center py-6">
                  No pages extracted yet.
                </div>
              )}
            </div>
            
            <div className="mt-4 pt-4 border-t border-slate-100">
              <div className="flex justify-between text-xs text-slate-500 mb-1">
                <span>Total Chars:</span>
                <span className="font-medium text-slate-700">{totalExtractedChars.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-xs text-slate-500">
                <span>OCR Status:</span>
                <span className="font-medium text-slate-700 capitalize">{document.upload_status}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right side: Extracted Text Viewer */}
        <div className="md:col-span-9">
          <div className="bg-white rounded-xl border border-border shadow-sm flex flex-col h-full min-h-[500px]">
            <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-slate-50/50 rounded-t-xl">
              <h2 className="font-semibold text-slate-800">
                Extracted Text {activePage ? `- Page ${activePage.page_number}` : ''}
              </h2>
              {activePage?.extraction_method && (
                <span className="text-xs text-slate-500 font-medium px-2 py-1 bg-white border border-slate-200 rounded-md shadow-sm">
                  Method: {activePage.extraction_method}
                </span>
              )}
            </div>
            
            <div className="p-6 flex-1 bg-[#fcfdfd]">
              {activePage ? (
                activePage.status === "completed" ? (
                  activePage.extracted_text ? (
                    <div className="whitespace-pre-wrap font-mono text-sm text-slate-700 leading-relaxed custom-scrollbar h-[500px] overflow-y-auto">
                      {activePage.extracted_text}
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-full text-slate-400 gap-2">
                      <FileText className="h-8 w-8 opacity-20" />
                      <p>No text found on this page.</p>
                    </div>
                  )
                ) : activePage.status === "failed" ? (
                  <div className="flex flex-col items-center justify-center h-full text-red-400 gap-2">
                    <p>OCR failed for this page.</p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-slate-400 gap-3">
                    <Loader2 className="h-6 w-6 animate-spin text-primary/50" />
                    <p>Processing page...</p>
                  </div>
                )
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-slate-400 gap-2">
                  <p>Select a page to view extracted text.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
