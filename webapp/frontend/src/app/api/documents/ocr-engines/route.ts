import { forward } from "@/lib/backend";

export async function GET() {
  return forward("/documents/ocr-engines", { fallback: "Failed to fetch OCR engines", auth: false });
}
