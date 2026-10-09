"use client";

import { LayoutDashboard, CreditCard, Settings, Edit3, ClipboardCheck, Coins } from "lucide-react";
import { AppSidebar, type SidebarItem } from "@/components/layout/sidebar";

const items: SidebarItem[] = [
  { name: "Overview", href: "/admin", icon: LayoutDashboard, exact: true },
  { name: "Tiers", href: "/admin/tiers", icon: CreditCard, exact: false },
  { name: "Model Rates", href: "/admin/rates", icon: Coins, exact: false },
  { name: "Configuration", href: "/admin/config", icon: Settings, exact: false },
  { name: "Annotations", href: "/admin/annotations", icon: Edit3, exact: false },
  { name: "Approved Annotations", href: "/admin/approved-annotations", icon: ClipboardCheck, exact: false },
];

export function AdminSidebar() {
  return <AppSidebar label="Admin Panel" items={items} />;
}
