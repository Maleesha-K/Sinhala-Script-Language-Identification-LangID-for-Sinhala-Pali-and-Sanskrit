import { redirect } from "next/navigation";
import { cookies } from "next/headers";
import { DashboardSidebar } from "@/components/dashboard/sidebar";
import { AppHeader } from "@/components/layout/app-header";
import { SidebarProvider } from "@/components/layout/sidebar";
import { SIDEBAR_COOKIE } from "@/lib/sidebar";
import axios from "axios";
import { API_URL } from "@/lib/backend";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;

  if (!token) {
    redirect("/auth/login");
  }

  // redirect() throws, so it must stay outside the try/catch.
  let role: string | null = null;
  try {
    const res = await axios.get(`${API_URL}/users/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    role = res.data.data.role;
  } catch {
    redirect("/auth/login");
  }
  // Admins work in the admin panel only.
  if (role === "admin") {
    redirect("/admin");
  }

  return (
    <SidebarProvider defaultCollapsed={cookieStore.get(SIDEBAR_COOKIE)?.value === "true"}>
      <div className="flex flex-col h-screen overflow-hidden">
        <AppHeader />
        <div className="flex flex-1 overflow-hidden">
          <DashboardSidebar />
          <main className="flex-1 min-w-0 overflow-y-auto">
            {/* Wide enough for side-by-side work; capped so lines stay readable on huge screens. */}
            <div className="mx-auto w-full max-w-[1600px] px-4 py-6 sm:px-6 lg:px-8 space-y-6">
              {children}
            </div>
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
