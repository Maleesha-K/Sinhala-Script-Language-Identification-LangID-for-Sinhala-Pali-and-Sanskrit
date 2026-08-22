"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  CreditCard,
  Settings,
  Edit3,
} from "lucide-react";
import { cn } from "@/lib/utils";

const items = [
  { name: "Overview", href: "/admin", icon: LayoutDashboard, exact: true },
  { name: "Tiers", href: "/admin/tiers", icon: CreditCard, exact: false },
  { name: "Configuration", href: "/admin/config", icon: Settings, exact: false },
  { name: "Annotations", href: "/admin/annotations", icon: Edit3, exact: false },
];

export function AdminSidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-60 shrink-0 border-r border-border bg-sidebar h-[calc(100vh-64px)] hidden md:flex flex-col">
      <div className="flex-1 p-3 py-5 space-y-0.5">
        <p className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">
          Admin Panel
        </p>
        <nav className="space-y-0.5">
          {items.map((item) => {
            const active = item.exact
              ? pathname === item.href
              : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-all duration-150",
                  active
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-sidebar-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                <item.icon className="h-4 w-4 shrink-0" />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
