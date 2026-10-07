"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { PageHeader } from "@/components/layout/page-header";
import { Users, CreditCard, Activity, Database, Edit3, Settings, Coins } from "lucide-react";
import Link from "next/link";

type Stats = {
  total_users: number;
  active_subscriptions: number;
  storage_used_bytes: number;
  active_jobs: number;
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let value = bytes / 1024;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit++;
  }
  return `${value.toFixed(1)} ${units[unit]}`;
}

const quickLinks = [
  { href: "/admin/tiers", icon: CreditCard, label: "Manage Tiers", desc: "Create and edit subscription plans." },
  { href: "/admin/rates", icon: Coins, label: "Model Rates", desc: "Set credit costs for OCR and classification models." },
  { href: "/admin/config", icon: Settings, label: "System Config", desc: "Set exchange rates and platform settings." },
  { href: "/admin/annotations", icon: Edit3, label: "Review Annotations", desc: "Approve or reject user corrections." },
];

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    axios
      .get("/api/admin/stats")
      .then((res) => setStats(res.data))
      .catch(() => setStats(null));
  }, []);

  const cards = [
    { label: "Total Users", value: stats?.total_users.toLocaleString(), sub: "All registered users", icon: Users },
    { label: "Active Subscriptions", value: stats?.active_subscriptions.toLocaleString(), sub: "Paid tier accounts", icon: CreditCard },
    { label: "Storage Used", value: stats ? formatBytes(stats.storage_used_bytes) : undefined, sub: "Across all documents", icon: Database },
    { label: "Active Jobs", value: stats?.active_jobs.toLocaleString(), sub: "Running or queued", icon: Activity },
  ];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Admin Dashboard"
        description="Platform overview and system management."
      />

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map(({ label, value, sub, icon: Icon }) => (
          <div key={label} className="rounded-xl border border-border bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">{label}</p>
              <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
                <Icon className="h-4 w-4 text-primary" />
              </div>
            </div>
            <p className="text-2xl font-bold text-foreground">{value ?? "—"}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>
          </div>
        ))}
      </div>

      {/* Quick links */}
      <div>
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickLinks.map(({ href, icon: Icon, label, desc }) => (
            <Link
              key={href}
              href={href}
              className="group rounded-xl border border-border bg-white p-5 shadow-sm hover:border-primary/40 hover:shadow-md transition-all"
            >
              <div className="h-9 w-9 rounded-lg bg-primary/10 flex items-center justify-center mb-3 group-hover:bg-primary/20 transition-colors">
                <Icon className="h-4 w-4 text-primary" />
              </div>
              <p className="font-semibold text-sm mb-1 group-hover:text-primary transition-colors">{label}</p>
              <p className="text-xs text-muted-foreground">{desc}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
