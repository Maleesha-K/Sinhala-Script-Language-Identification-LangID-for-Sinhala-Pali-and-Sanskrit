import { redirect } from "next/navigation";
import { cookies } from "next/headers";
import { AdminSidebar } from "@/components/admin/sidebar";
import axios from "axios";

// This layout enforces that only Admins can view the /admin/* routes.
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
    // Validate the user's role by hitting the backend directly.
    const res = await axios.get("http://localhost:8000/api/v1/users/me", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const user = res.data.data;
    if (user.role !== "admin") {
      redirect("/dashboard"); // Redirect non-admins to the regular dashboard
    }
  } catch (error) {
    redirect("/auth/login");
  }

  return (
    <div className="flex min-h-[calc(100vh-64px)]">
      <AdminSidebar />
      <main className="flex-1 overflow-y-auto bg-background/50">
        <div className="container p-6 lg:p-8">{children}</div>
      </main>
    </div>
  );
}
