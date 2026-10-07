import { forward } from "@/lib/backend";

export async function GET() {
  return forward("/admin/stats", { unwrap: true, fallback: "Failed to fetch platform stats" });
}
