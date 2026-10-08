import { forward } from "@/lib/backend";

export async function POST(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return forward(`/documents/${id}/cancel`, { method: "POST", unwrap: true, fallback: "Failed to cancel processing" });
}
