import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import axios from "axios";

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;
    const cookieStore = await cookies();
    const token = cookieStore.get("access_token")?.value;

    if (!token) {
      return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const response = await axios.get(`${apiUrl}/documents/${id}/download`, {
      headers: { Authorization: `Bearer ${token}` }
    });

    return NextResponse.json(response.data.data);
  } catch (error: any) {
    return NextResponse.json(
      { detail: error.response?.data?.message || 'Failed to generate download URL' },
      { status: error.response?.status || 500 }
    );
  }
}
