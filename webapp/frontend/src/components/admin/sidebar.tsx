"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Users, CreditCard, Settings, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

const items = [
  { name: "Dashboard", href: "/admin", icon: LayoutDashboard },
  { name: "Tiers", href: "/admin/tiers", icon: CreditCard },
  { name: "System Config", href: "/admin/config", icon: Settings },
  { name: "Users", href: "/admin/users", icon: Users },
  { name: "Annotations", href: "/admin/annotations", icon: FileText },
];

export function AdminSidebar() {
  const pathname = usePathname();

  return (
    <div className="w-64 border-r bg-muted/20 h-[calc(100vh-64px)] hidden md:block">
      <div className="p-4 py-6 space-y-2">
        <h2 className="px-4 text-xs font-semibold tracking-tight text-muted-foreground uppercase">
          Admin Panel
        </h2>
        <nav className="space-y-1">
          {items.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                pathname === item.href
                  ? "bg-secondary text-secondary-foreground"
                  : "text-muted-foreground hover:bg-secondary/50 hover:text-primary"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.name}
            </Link>
          ))}
        </nav>
      </div>
    </div>
  );
}
