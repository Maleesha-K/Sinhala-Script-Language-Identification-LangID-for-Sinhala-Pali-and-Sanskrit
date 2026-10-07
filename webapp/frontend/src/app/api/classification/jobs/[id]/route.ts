import { forward } from "@/lib/backend";

export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return forward(`/classification/jobs/${id}`, { fallback: "Failed to fetch job" });
}
