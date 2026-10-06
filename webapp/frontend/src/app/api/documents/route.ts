import { forward } from "@/lib/backend";

export async function GET() {
  return forward("/documents", { unwrap: true, fallback: "Failed to fetch documents" });
}

export async function POST(request: Request) {
  // Passed through as FormData so axios sets the multipart boundary itself.
  const formData = await request.formData();
  return forward("/documents/upload", { method: "POST", body: formData, unwrap: true, fallback: "Failed to upload document" });
}
