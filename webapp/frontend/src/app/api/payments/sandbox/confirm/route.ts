import { forward } from "@/lib/backend";

export async function POST(request: Request) {
  return forward("/payments/sandbox/confirm", { method: "POST", body: await request.json(), fallback: "Failed to confirm sandbox payment" });
}
