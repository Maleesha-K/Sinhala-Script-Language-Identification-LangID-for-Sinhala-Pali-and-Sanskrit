import { forward } from "@/lib/backend";

export async function GET() {
  return forward("/admin/config", { unwrap: true, fallback: "Failed to fetch config" });
}

export async function PUT(request: Request) {
  return forward("/admin/config", { method: "PUT", body: await request.json(), unwrap: true, fallback: "Failed to update config" });
}
