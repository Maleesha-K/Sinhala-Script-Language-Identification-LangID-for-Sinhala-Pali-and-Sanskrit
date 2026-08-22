"use client";

import { useAuth } from "@/context/auth-context";
import { PageHeader } from "@/components/layout/page-header";
import { FileText, Activity, CheckCircle2, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

const quickLinks = [
  {
    href: "/dashboard/documents",
    icon: FileText,
    label: "Documents",
    desc: "Upload PDFs and manage your document library.",
    cta: "Manage Documents",
  },
  {
    href: "/dashboard/classification",
    icon: Activity,
    label: "Language ID",
    desc: "Paste text and identify Sinhala, Pali, or Sanskrit.",
    cta: "Run Classification",
  },
];

export default function DashboardOverviewPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-8">
      <PageHeader
        title={`Welcome back${user?.email ? `, ${user.email.split("@")[0]}` : ""}`}
        description="Here's an overview of your LangID workspace."
      />

      {/* Quick access cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {quickLinks.map(({ href, icon: Icon, label, desc, cta }) => (
          <div key={href} className="rounded-xl border border-border bg-white p-6 shadow-sm hover:border-primary/40 hover:shadow-md transition-all group">
            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
              <Icon className="h-5 w-5 text-primary" />
            </div>
            <h3 className="font-semibold text-sm mb-1">{label}</h3>
            <p className="text-muted-foreground text-sm mb-4">{desc}</p>
            <Link href={href}>
              <Button size="sm" variant="outline" className="text-xs border-primary/30 text-primary hover:bg-primary hover:text-primary-foreground transition-colors">
                {cta}
              </Button>
            </Link>
          </div>
        ))}
      </div>

      {/* Info banner */}
      <div className="rounded-xl border border-primary/20 bg-primary/5 px-5 py-4 flex items-start gap-4">
        <CheckCircle2 className="h-5 w-5 text-primary mt-0.5 shrink-0" />
        <div>
          <p className="text-sm font-medium text-foreground">Help improve LangID</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            After running a classification job, you can click any segment to report a misclassification. Your corrections help retrain the model.
          </p>
        </div>
      </div>

      {user?.role === "admin" && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-5 py-4 flex items-start gap-4">
          <ShieldCheck className="h-5 w-5 text-amber-600 mt-0.5 shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-medium text-amber-900">You have admin privileges</p>
            <p className="text-xs text-amber-700 mt-0.5">
              Use the Admin Panel to manage tiers, system configuration, and review user annotations.
            </p>
          </div>
          <Link href="/admin">
            <Button size="sm" className="text-xs bg-amber-600 hover:bg-amber-700 text-white shrink-0">
              Admin Panel
            </Button>
          </Link>
        </div>
      )}
    </div>
  );
}
