import { forward } from "@/lib/backend";

export async function GET() {
  return forward("/admin-rates", { fallback: "Failed to fetch rates" });
}

export async function POST(request: Request) {
  return forward("/admin-rates", { method: "POST", body: await request.json(), fallback: "Failed to create rate" });
}
