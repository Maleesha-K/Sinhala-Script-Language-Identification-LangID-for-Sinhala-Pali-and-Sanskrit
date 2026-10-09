import { NextResponse } from "next/server";
import axios from "axios";
import { getValidToken } from "@/lib/auth-server";
import { API_URL, backendErrorMessage } from "@/lib/backend";

/** The original PDF page as a PNG. Binary, so it bypasses `forward`'s JSON. */
export async function GET(_request: Request, { params }: { params: Promise<{ id: string; page: string }> }) {
  const { id, page } = await params;
  const token = await getValidToken();
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  try {
    const res = await axios.get<ArrayBuffer>(`${API_URL}/documents/${id}/pages/${page}/image`, {
      headers: { Authorization: `Bearer ${token}` },
      responseType: "arraybuffer",
    });
    return new Response(res.data, {
      headers: {
        "Content-Type": String(res.headers["content-type"] ?? "image/png"),
        "Cache-Control": String(res.headers["cache-control"] ?? "private, max-age=86400"),
      },
    });
  } catch (error) {
    const status = axios.isAxiosError(error) ? error.response?.status ?? 502 : 500;
    return NextResponse.json({ detail: backendErrorMessage(error, "Failed to load page image") }, { status });
  }
}
