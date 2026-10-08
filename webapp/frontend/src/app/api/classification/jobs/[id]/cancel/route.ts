import { forward } from "@/lib/backend";

export async function POST(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return forward(`/classification/jobs/${id}/cancel`, { method: "POST", fallback: "Failed to cancel the job" });
}
