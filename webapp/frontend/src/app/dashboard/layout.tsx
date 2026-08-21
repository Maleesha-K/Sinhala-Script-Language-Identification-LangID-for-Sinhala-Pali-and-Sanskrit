import { redirect } from "next/navigation";
import { cookies } from "next/headers";
import { DashboardSidebar } from "@/components/dashboard/sidebar";
import axios from "axios";

// This layout enforces that only authenticated users can view the /dashboard/* routes.
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

  try {
    // Optionally pre-fetch user data here, but for now we just verify token validity
    await axios.get("http://localhost:8000/api/v1/users/me", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  } catch (error) {
    redirect("/auth/login");
  }

  return (
    <div className="flex min-h-[calc(100vh-64px)]">
      <DashboardSidebar />
      <main className="flex-1 overflow-y-auto bg-background/50">
        <div className="container p-6 lg:p-8">{children}</div>
      </main>
    </div>
  );
}
