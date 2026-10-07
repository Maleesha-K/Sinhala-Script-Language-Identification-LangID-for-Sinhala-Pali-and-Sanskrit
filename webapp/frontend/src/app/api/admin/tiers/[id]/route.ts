import { forward } from "@/lib/backend";

export async function PUT(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return forward(`/admin/tiers/${id}`, { method: "PUT", body: await request.json(), unwrap: true, fallback: "Failed to update tier" });
}

export async function DELETE(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return forward(`/admin/tiers/${id}`, { method: "DELETE", unwrap: true, fallback: "Failed to delete tier" });
}
