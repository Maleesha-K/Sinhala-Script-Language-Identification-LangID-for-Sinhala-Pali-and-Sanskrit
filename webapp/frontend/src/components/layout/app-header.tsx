"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Globe,
  LayoutDashboard,
  ShieldCheck,
  LogOut,
  User,
  ChevronDown,
  Loader2,
  Coins,
} from "lucide-react";
import { useAuth } from "@/context/auth-context";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function AppHeader() {
  const { user, loading, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const isAdmin = user?.role === "admin";
  const inAdminSection = pathname.startsWith("/admin");

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white/95 backdrop-blur-md shadow-sm">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link
            href={user ? "/dashboard" : "/"}
            className="flex items-center gap-2 group"
          >
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center shadow-sm group-hover:bg-primary/90 transition-colors">
              <Globe className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="font-bold text-lg tracking-tight text-foreground">
              LangID
            </span>
          </Link>

          {/* Right side */}
          <div className="flex items-center gap-3">
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            ) : user ? (
              <>
                {/* Role switcher pill */}
                {isAdmin && (
                  <Link href={inAdminSection ? "/dashboard" : "/admin"}>
                    <Button
                      variant="outline"
                      size="sm"
                      className={cn(
                        "gap-2 text-xs font-semibold border-primary/30 transition-all",
                        inAdminSection
                          ? "bg-primary text-primary-foreground hover:bg-primary/90 border-primary"
                          : "text-primary hover:bg-accent",
                      )}
                    >
                      {inAdminSection ? (
                        <>
                          <LayoutDashboard className="h-3.5 w-3.5" />
                          User Dashboard
                        </>
                      ) : (
                        <>
                          <ShieldCheck className="h-3.5 w-3.5" />
                          Admin Panel
                        </>
                      )}
                    </Button>
                  </Link>
                )}

                {/* Credits Pill */}
                <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/50 shadow-sm">
                  <Coins className="h-3.5 w-3.5" />
                  <span className="text-xs font-bold tracking-tight">
                    {user.credits_balance?.toLocaleString() || "0"}{" "}
                    <span className="font-medium opacity-80">credits</span>
                  </span>
                </div>

                {/* User dropdown — base-ui DropdownMenu doesn't use asChild */}
                <DropdownMenu>
                  <DropdownMenuTrigger
                    className={cn(
                      "flex items-center gap-2 rounded-md px-2 py-1.5 text-sm font-medium",
                      "hover:bg-accent transition-colors focus-visible:outline-none",
                    )}
                  >
                    <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center">
                      <User className="h-3.5 w-3.5 text-primary" />
                    </div>
                    <span className="hidden sm:inline max-w-[140px] truncate">
                      {user.email}
                    </span>
                    <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-56">
                    <DropdownMenuGroup>
                      <DropdownMenuLabel className="font-normal">
                        <div className="flex flex-col space-y-1">
                          <p className="text-sm font-semibold leading-none">
                            {user.email}
                          </p>
                          <p className="text-xs text-muted-foreground capitalize">
                            {user.role} account
                          </p>
                        </div>
                      </DropdownMenuLabel>
                    </DropdownMenuGroup>
                    <DropdownMenuSeparator />
                    {/* base-ui DropdownMenuItem uses onClick, not asChild */}
                    <DropdownMenuItem
                      onClick={() => router.push("/dashboard")}
                      className="flex items-center gap-2 cursor-pointer"
                    >
                      <LayoutDashboard className="h-4 w-4" />
                      Dashboard
                    </DropdownMenuItem>
                    {isAdmin && (
                      <DropdownMenuItem
                        onClick={() => router.push("/admin")}
                        className="flex items-center gap-2 cursor-pointer"
                      >
                        <ShieldCheck className="h-4 w-4" />
                        Admin Panel
                      </DropdownMenuItem>
                    )}
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      onClick={logout}
                      variant="destructive"
                      className="flex items-center gap-2 cursor-pointer"
                    >
                      <LogOut className="h-4 w-4" />
                      Log out
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <Link href="/auth/login">
                  <Button variant="ghost" size="sm" className="font-medium">
                    Log In
                  </Button>
                </Link>
                <Link href="/auth/signup">
                  <Button size="sm" className="font-medium shadow-sm">
                    Sign Up
                  </Button>
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
