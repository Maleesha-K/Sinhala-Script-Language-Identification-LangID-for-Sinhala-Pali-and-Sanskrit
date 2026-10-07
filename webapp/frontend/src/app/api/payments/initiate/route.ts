import { forward } from "@/lib/backend";

export async function POST(request: Request) {
  return forward("/payments/payhere/initiate", { method: "POST", body: await request.json(), fallback: "Failed to initiate payment" });
}
