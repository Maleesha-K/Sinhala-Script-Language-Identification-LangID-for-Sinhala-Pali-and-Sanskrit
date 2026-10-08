import { redirect } from "next/navigation";
import { cookies } from "next/headers";
import { DashboardSidebar } from "@/components/dashboard/sidebar";
import { AppHeader } from "@/components/layout/app-header";
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
    <div className="flex flex-col h-screen overflow-hidden">
      <AppHeader />
      <div className="flex flex-1 overflow-hidden">
        <DashboardSidebar />
        <main className="flex-1 overflow-y-auto">
          <div className="container max-w-6xl mx-auto p-6 lg:p-8 space-y-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
