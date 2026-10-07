import { forward } from "@/lib/backend";

export async function GET() {
  return forward("/payments/packages", { auth: false, fallback: "Failed to fetch packages" });
}
