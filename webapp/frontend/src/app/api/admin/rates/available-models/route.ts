import { forward } from "@/lib/backend";

export async function GET() {
  return forward("/admin-rates/available-models", { fallback: "Failed to fetch available models" });
}
