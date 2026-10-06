import { forward } from "@/lib/backend";

export async function GET() {
  return forward("/admin/tiers", { unwrap: true, fallback: "Failed to fetch tiers" });
}

export async function POST(request: Request) {
  return forward("/admin/tiers", { method: "POST", body: await request.json(), unwrap: true, fallback: "Failed to create tier" });
}
