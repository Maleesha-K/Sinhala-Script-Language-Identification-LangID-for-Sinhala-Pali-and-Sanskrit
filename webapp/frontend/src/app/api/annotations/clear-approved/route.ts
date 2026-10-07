import { forward } from "@/lib/backend";

export async function POST(request: Request) {
  return forward("/annotations/clear-approved", { method: "POST", body: await request.json(), fallback: "Failed to clear approved annotations" });
}
