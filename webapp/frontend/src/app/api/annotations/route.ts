import { forward } from "@/lib/backend";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const params: Record<string, string> = { pending_only: searchParams.get("pending_only") || "true" };
  for (const key of ["approved_only", "skip", "limit"]) {
    const value = searchParams.get(key);
    if (value !== null) params[key] = value;
  }
  return forward("/annotations", { params, fallback: "Failed to fetch annotations" });
}

export async function POST(request: Request) {
  return forward("/annotations", { method: "POST", body: await request.json(), fallback: "Failed to submit correction" });
}
