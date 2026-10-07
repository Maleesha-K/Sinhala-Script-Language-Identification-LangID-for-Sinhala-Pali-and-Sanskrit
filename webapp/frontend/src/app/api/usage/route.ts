import { forward } from "@/lib/backend";

export async function GET() {
  return forward("/usage/breakdown", { fallback: "Failed to fetch usage breakdown" });
}
