import { forward } from "@/lib/backend";

export async function GET() {
  return forward("/payments/history", { fallback: "Failed to fetch payment history" });
}
