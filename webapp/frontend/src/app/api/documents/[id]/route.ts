import { forward } from "@/lib/backend";

export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return forward(`/documents/${id}`, { unwrap: true, fallback: "Failed to fetch document" });
}

export async function DELETE(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return forward(`/documents/${id}`, { method: "DELETE", fallback: "Failed to delete document" });
}
