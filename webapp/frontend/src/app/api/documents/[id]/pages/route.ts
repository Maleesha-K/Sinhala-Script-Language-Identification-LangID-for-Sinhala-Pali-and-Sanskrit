import { NextResponse } from "next/server";
import { getValidToken } from "@/lib/auth-server";
import axios from "axios";

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;
    const token = await getValidToken();

    if (!token) {
      return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const response = await axios.get(`${apiUrl}/documents/${id}/pages`, {
      headers: { Authorization: `Bearer ${token}` }
    });

    return NextResponse.json(response.data.data);
  } catch (error: any) {
    return NextResponse.json(
      { detail: error.response?.data?.message || 'Failed to fetch document pages' },
      { status: error.response?.status || 500 }
    );
  }
}
