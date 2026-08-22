import { redirect } from "next/navigation";
import { cookies } from "next/headers";
import { AdminSidebar } from "@/components/admin/sidebar";
import { AppHeader } from "@/components/layout/app-header";
import axios from "axios";

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;

  if (!token) {
    redirect("/auth/login");
  }

  try {
    const res = await axios.get("http://localhost:8000/api/v1/users/me", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const user = res.data.data;
    if (user.role !== "admin") {
      redirect("/dashboard");
    }
  } catch {
    redirect("/auth/login");
  }

  return (
    <div className="flex flex-col min-h-screen">
      <AppHeader />
      <div className="flex flex-1 overflow-hidden">
        <AdminSidebar />
        <main className="flex-1 overflow-y-auto">
          <div className="container max-w-6xl mx-auto p-6 lg:p-8 space-y-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
