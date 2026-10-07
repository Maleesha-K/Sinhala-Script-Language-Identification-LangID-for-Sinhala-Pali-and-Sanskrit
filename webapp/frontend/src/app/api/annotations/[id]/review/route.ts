import { forward } from "@/lib/backend";

export async function PUT(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return forward(`/annotations/${id}/review`, { method: "PUT", body: await request.json(), fallback: "Failed to review annotation" });
}
