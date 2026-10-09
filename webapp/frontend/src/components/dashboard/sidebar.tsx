"use client";

import { LayoutDashboard, FileText, Activity, BarChart2 } from "lucide-react";
import { AppSidebar, type SidebarItem } from "@/components/layout/sidebar";

const items: SidebarItem[] = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard, exact: true },
  { name: "Documents", href: "/dashboard/documents", icon: FileText, exact: false },
  { name: "Language ID", href: "/dashboard/classification", icon: Activity, exact: false },
  { name: "Usage", href: "/dashboard/usage", icon: BarChart2, exact: false },
];

export function DashboardSidebar() {
  return <AppSidebar label="Navigation" items={items} />;
}
