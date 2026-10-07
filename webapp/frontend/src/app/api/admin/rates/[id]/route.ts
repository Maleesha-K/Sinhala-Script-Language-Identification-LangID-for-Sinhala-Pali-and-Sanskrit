import { forward } from "@/lib/backend";

export async function PUT(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return forward(`/admin-rates/${id}`, { method: "PUT", body: await request.json(), fallback: "Failed to update rate" });
}

export async function DELETE(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return forward(`/admin-rates/${id}`, { method: "DELETE", fallback: "Failed to delete rate" });
}
