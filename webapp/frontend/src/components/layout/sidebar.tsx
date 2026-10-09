"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { LucideIcon } from "lucide-react";
import { PanelLeftClose, PanelLeftOpen, Menu, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { SIDEBAR_COOKIE } from "@/lib/sidebar";


type SidebarState = {
  /** Desktop: the sidebar shows icons only. */
  collapsed: boolean;
  toggleCollapsed: () => void;
  /** Mobile: the sidebar is open as a drawer over the page. */
  mobileOpen: boolean;
  setMobileOpen: (open: boolean) => void;
};

const SidebarContext = createContext<SidebarState | null>(null);

/** The sidebar's state, or null outside a layout with a sidebar. */
export function useSidebar() {
  return useContext(SidebarContext);
}

export function SidebarProvider({
  defaultCollapsed = false,
  children,
}: {
  defaultCollapsed?: boolean;
  children: React.ReactNode;
}) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);
  const [mobileOpen, setMobileOpen] = useState(false);

  const toggleCollapsed = useCallback(() => {
    setCollapsed((prev) => {
      window.document.cookie = `${SIDEBAR_COOKIE}=${!prev}; path=/; max-age=31536000; samesite=lax`;
      return !prev;
    });
  }, []);

  // Ctrl/Cmd+B toggles the sidebar, as in most editors.
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key.toLowerCase() === "b" && (event.metaKey || event.ctrlKey) && !event.altKey && !event.shiftKey) {
        event.preventDefault();
        if (window.matchMedia("(min-width: 768px)").matches) toggleCollapsed();
        else setMobileOpen((open) => !open);
      }
      if (event.key === "Escape") setMobileOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [toggleCollapsed]);

  return (
    <SidebarContext.Provider value={{ collapsed, toggleCollapsed, mobileOpen, setMobileOpen }}>
      {children}
    </SidebarContext.Provider>
  );
}

/** The header button: collapses the sidebar on desktop, opens the drawer on mobile. */
export function SidebarTrigger() {
  const sidebar = useSidebar();
  if (!sidebar) return null;
  const { collapsed, toggleCollapsed, mobileOpen, setMobileOpen } = sidebar;
  const button = "h-9 w-9 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-foreground transition-colors";
  return (
    <>
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        aria-label={mobileOpen ? "Close menu" : "Open menu"}
        aria-expanded={mobileOpen}
        className={cn("flex md:hidden", button)}
      >
        {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </button>
      <Tooltip>
        <TooltipTrigger
          render={
            <button
              onClick={toggleCollapsed}
              aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
              aria-expanded={!collapsed}
              className={cn("hidden md:flex", button)}
            />
          }
        >
          {collapsed ? <PanelLeftOpen className="h-[18px] w-[18px]" /> : <PanelLeftClose className="h-[18px] w-[18px]" />}
        </TooltipTrigger>
        <TooltipContent side="bottom">
          {collapsed ? "Expand sidebar" : "Collapse sidebar"}
          <kbd data-slot="kbd" className="ml-1 rounded bg-background/20 px-1 font-sans text-[10px]">Ctrl B</kbd>
        </TooltipContent>
      </Tooltip>
    </>
  );
}

export type SidebarItem = {
  name: string;
  href: string;
  icon: LucideIcon;
  /** Active only on this exact path, not its sub-pages. */
  exact: boolean;
};

export function AppSidebar({ label, items }: { label: string; items: SidebarItem[] }) {
  const pathname = usePathname();
  const sidebar = useSidebar();
  const collapsed = sidebar?.collapsed ?? false;
  const mobileOpen = sidebar?.mobileOpen ?? false;
  const closeMobile = () => sidebar?.setMobileOpen(false);

  const nav = (iconOnly: boolean) => (
    <nav className="space-y-0.5">
      {items.map((item) => {
        const active = item.exact ? pathname === item.href : pathname.startsWith(item.href);
        const linkProps = {
          href: item.href,
          onClick: closeMobile,
          "aria-current": active ? ("page" as const) : undefined,
          className: cn(
            "flex items-center gap-3 rounded-md py-2 text-sm font-medium transition-colors duration-150",
            iconOnly ? "justify-center px-0" : "px-3",
            active
              ? "bg-primary text-primary-foreground shadow-sm"
              : "text-sidebar-foreground hover:bg-accent hover:text-accent-foreground",
          ),
        };
        // Icons alone are named by a tooltip.
        return iconOnly ? (
          <Tooltip key={item.href}>
            <TooltipTrigger render={<Link {...linkProps} aria-label={item.name} />}>
              <item.icon className="h-4 w-4 shrink-0" />
            </TooltipTrigger>
            <TooltipContent side="right">{item.name}</TooltipContent>
          </Tooltip>
        ) : (
          <Link key={item.href} {...linkProps}>
            <item.icon className="h-4 w-4 shrink-0" />
            <span className="truncate">{item.name}</span>
          </Link>
        );
      })}
    </nav>
  );

  return (
    <>
      {/* Desktop: a full sidebar, or an icon rail when collapsed. */}
      <aside
        className={cn(
          "shrink-0 border-r border-border bg-sidebar hidden md:flex flex-col transition-[width] duration-200 ease-out",
          collapsed ? "w-16" : "w-56",
        )}
      >
        <div className={cn("flex-1 py-5 overflow-y-auto overflow-x-hidden", collapsed ? "px-2.5" : "px-3")}>
          {collapsed ? (
            <div className="mx-auto mb-3 h-px w-6 bg-border" aria-hidden />
          ) : (
            <p className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-muted-foreground uppercase whitespace-nowrap">
              {label}
            </p>
          )}
          {nav(collapsed)}
        </div>
      </aside>

      {/* Mobile: a drawer over the page. */}
      <div
        className={cn("fixed inset-0 top-16 z-40 md:hidden", !mobileOpen && "pointer-events-none")}
        aria-hidden={!mobileOpen}
      >
        <div
          onClick={closeMobile}
          className={cn("absolute inset-0 bg-black/30 transition-opacity", mobileOpen ? "opacity-100" : "opacity-0")}
        />
        <aside
          inert={!mobileOpen}
          className={cn(
            "absolute inset-y-0 left-0 w-64 max-w-[80vw] border-r border-border bg-sidebar px-3 py-5 shadow-xl transition-transform duration-200 ease-out",
            mobileOpen ? "translate-x-0" : "-translate-x-full",
          )}
        >
          <p className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">{label}</p>
          {nav(false)}
        </aside>
      </div>
    </>
  );
}
