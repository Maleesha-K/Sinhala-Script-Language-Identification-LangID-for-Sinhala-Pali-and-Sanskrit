"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import axios from "axios";
import { formatDistanceToNow } from "date-fns";
import {
  FileText, Activity, CheckCircle2, Coins, ArrowRight, Loader2, XCircle, Clock, Upload,
} from "lucide-react";
import { useAuth } from "@/context/auth-context";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Job = {
  id: string;
  status: "queued" | "processing" | "completed" | "failed";
  model_name: string;
  total_tokens: number;
  created_at: string;
};

type Document = {
  id: string;
  filename: string;
  upload_status: "uploading" | "ready" | "failed" | "deleted";
  created_at: string;
};

// The jobs endpoint returns the most recent 20.
const JOB_PAGE = 20;
const RECENT = 5;

const STATUS = {
  queued:     { icon: Clock,        className: "text-amber-500",   label: "Queued" },
  processing: { icon: Loader2,      className: "text-primary",     label: "Processing" },
  uploading:  { icon: Loader2,      className: "text-primary",     label: "Processing" },
  completed:  { icon: CheckCircle2, className: "text-emerald-500", label: "Completed" },
  ready:      { icon: CheckCircle2, className: "text-emerald-500", label: "Ready" },
  failed:     { icon: XCircle,      className: "text-destructive", label: "Failed" },
  deleted:    { icon: XCircle,      className: "text-destructive", label: "Deleted" },
} as const;

function StatusIcon({ status }: { status: keyof typeof STATUS }) {
  const { icon: Icon, className, label } = STATUS[status] ?? STATUS.queued;
  return <Icon className={cn("h-4 w-4 shrink-0", className, Icon === Loader2 && "animate-spin")} aria-label={label} />;
}

const ago = (date: string) => formatDistanceToNow(new Date(date), { addSuffix: true });

export default function DashboardOverviewPage() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<Job[] | null>(null);
  const [documents, setDocuments] = useState<Document[] | null>(null);
  const [modelLabels, setModelLabels] = useState<Record<string, string>>({});

  useEffect(() => {
    axios.get("/api/classification/jobs").then((r) => setJobs(r.data?.data ?? [])).catch(() => setJobs([]));
    axios.get("/api/documents").then((r) => setDocuments(r.data ?? [])).catch(() => setDocuments([]));
    axios
      .get("/api/classification/models")
      .then((r) => setModelLabels(Object.fromEntries((r.data?.data ?? []).map((m: { id: string; label: string }) => [m.id, m.label]))))
      .catch(() => { /* show model ids */ });
  }, []);

  const name = user?.email ? user.email.split("@")[0] : "";
  const processingDocs = documents?.filter((d) => d.upload_status === "uploading").length ?? 0;
  const runningJobs = jobs?.filter((j) => j.status === "queued" || j.status === "processing").length ?? 0;

  return (
    <div className="space-y-8">
      <PageHeader
        title={`Welcome back${name ? `, ${name}` : ""}`}
        description="Identify Sinhala, Pali and Sanskrit in pasted text or scanned PDFs."
        actions={
          <div className="flex items-center gap-2">
            <Link href="/dashboard/documents">
              <Button variant="outline" className="gap-2"><Upload className="h-4 w-4" />Upload PDF</Button>
            </Link>
            <Link href="/dashboard/classification">
              <Button className="gap-2"><Activity className="h-4 w-4" />Classify Text</Button>
            </Link>
          </div>
        }
      />

      {/* At a glance */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Stat
          icon={Coins}
          tone="bg-emerald-50 text-emerald-600"
          label="Credit balance"
          value={user ? Number(user.credits_balance ?? 0).toLocaleString(undefined, { maximumFractionDigits: 2 }) : "—"}
          link={{ href: "/dashboard/usage", label: "Usage & top-up" }}
        />
        <Stat
          icon={FileText}
          tone="bg-blue-50 text-blue-600"
          label="Documents"
          value={documents ? documents.length.toLocaleString() : "—"}
          note={processingDocs ? `${processingDocs} processing` : undefined}
          link={{ href: "/dashboard/documents", label: "All documents" }}
        />
        <Stat
          icon={Activity}
          tone="bg-violet-50 text-violet-600"
          label="Text classifications"
          value={jobs ? (jobs.length >= JOB_PAGE ? `${JOB_PAGE}+` : jobs.length.toLocaleString()) : "—"}
          note={runningJobs ? `${runningJobs} running` : undefined}
          link={{ href: "/dashboard/classification", label: "New classification" }}
        />
      </div>

      {/* Recent activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecentList
          title="Recent classifications"
          loading={jobs === null}
          empty="No classifications yet. Paste some text to get started."
          emptyAction={{ href: "/dashboard/classification", label: "Classify text" }}
          items={(jobs ?? []).slice(0, RECENT).map((j) => ({
            key: j.id,
            href: `/dashboard/classification/${j.id}`,
            status: j.status,
            title: modelLabels[j.model_name] ?? j.model_name,
            meta: `${j.total_tokens ? `${j.total_tokens.toLocaleString()} tokens · ` : ""}${ago(j.created_at)}`,
          }))}
        />
        <RecentList
          title="Recent documents"
          loading={documents === null}
          empty="No documents yet. Upload a PDF to OCR it and identify its languages page by page."
          emptyAction={{ href: "/dashboard/documents", label: "Upload a PDF" }}
          items={(documents ?? []).slice(0, RECENT).map((d) => ({
            key: d.id,
            href: `/dashboard/documents/${d.id}`,
            status: d.upload_status,
            title: d.filename,
            meta: ago(d.created_at),
          }))}
        />
      </div>

      {/* Info banner */}
      <div className="rounded-xl border border-primary/20 bg-primary/5 px-5 py-4 flex items-start gap-4">
        <CheckCircle2 className="h-5 w-5 text-primary mt-0.5 shrink-0" />
        <div>
          <p className="text-sm font-medium text-foreground">Help improve LangID</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            In any result, click a sentence to report a misclassification. Your corrections help retrain the models.
          </p>
        </div>
      </div>
    </div>
  );
}

function Stat({
  icon: Icon, tone, label, value, note, link,
}: {
  icon: React.ElementType;
  tone: string;
  label: string;
  value: string;
  note?: string;
  link: { href: string; label: string };
}) {
  return (
    <div className="rounded-xl border border-border bg-white p-5 shadow-sm flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <div className={cn("h-9 w-9 rounded-lg flex items-center justify-center", tone)}>
          <Icon className="h-4.5 w-4.5" />
        </div>
        <p className="text-sm text-muted-foreground">{label}</p>
      </div>
      <div className="flex items-baseline gap-2">
        <p className="text-2xl font-bold tracking-tight tabular-nums">{value}</p>
        {note && <p className="text-xs font-medium text-primary">{note}</p>}
      </div>
      <Link href={link.href} className="text-xs font-medium text-primary hover:underline flex items-center gap-1 mt-auto">
        {link.label} <ArrowRight className="h-3 w-3" />
      </Link>
    </div>
  );
}

function RecentList({
  title, loading, empty, emptyAction, items,
}: {
  title: string;
  loading: boolean;
  empty: string;
  emptyAction: { href: string; label: string };
  items: { key: string; href: string; status: keyof typeof STATUS; title: string; meta: string }[];
}) {
  return (
    <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
      <div className="px-5 py-3.5 border-b border-border bg-slate-50/60">
        <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
      </div>
      {loading ? (
        <div className="flex justify-center py-10"><Loader2 className="h-5 w-5 animate-spin text-primary" /></div>
      ) : items.length === 0 ? (
        <div className="px-5 py-8 text-center space-y-3">
          <p className="text-sm text-muted-foreground">{empty}</p>
          <Link href={emptyAction.href}>
            <Button size="sm" variant="outline" className="text-xs">{emptyAction.label}</Button>
          </Link>
        </div>
      ) : (
        <ul className="divide-y divide-border">
          {items.map((item) => (
            <li key={item.key}>
              <Link href={item.href} className="flex items-center gap-3 px-5 py-3 hover:bg-slate-50 transition-colors group">
                <StatusIcon status={item.status} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium truncate">{item.title}</p>
                  <p className="text-xs text-muted-foreground">{item.meta}</p>
                </div>
                <ArrowRight className="h-4 w-4 text-slate-300 group-hover:text-primary transition-colors" />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
