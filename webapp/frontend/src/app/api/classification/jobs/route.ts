import { forward } from "@/lib/backend";

export async function POST(request: Request) {
  return forward("/classification/jobs", { method: "POST", body: await request.json(), fallback: "Failed to start classification" });
}

export async function GET() {
  return forward("/classification/jobs", { fallback: "Failed to fetch jobs" });
}
