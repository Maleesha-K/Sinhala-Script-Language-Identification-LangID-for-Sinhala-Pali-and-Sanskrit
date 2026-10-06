import { forward } from "@/lib/backend";

export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return forward(`/documents/${id}/pages`, { unwrap: true, fallback: "Failed to fetch document pages" });
}
