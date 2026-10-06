import { forward } from "@/lib/backend";

export async function GET() {
  return forward("/classification/models", { fallback: "Failed to fetch models" });
}
