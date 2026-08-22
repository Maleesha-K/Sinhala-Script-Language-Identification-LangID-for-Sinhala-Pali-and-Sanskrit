import { NextResponse } from "next/server";
import axios from "axios";
import { getValidToken } from "@/lib/auth-server";

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function PUT(request: Request, props: { params: Promise<{ id: string }> }) {
  try {
    const params = await props.params;
    const token = await getValidToken();
    if (!token) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

    const body = await request.json();
    const response = await axios.put(`${apiUrl}/admin/tiers/${params.id}`, body, {
      headers: { Authorization: `Bearer ${token}` }
    });

    return NextResponse.json(response.data.data);
  } catch (error: any) {
    return NextResponse.json(
      { detail: error.response?.data?.message || 'Failed to update tier' },
      { status: error.response?.status || 500 }
    );
  }
}

export async function DELETE(request: Request, props: { params: Promise<{ id: string }> }) {
  try {
    const params = await props.params;
    const token = await getValidToken();
    if (!token) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

    const response = await axios.delete(`${apiUrl}/admin/tiers/${params.id}`, {
      headers: { Authorization: `Bearer ${token}` }
    });

    return NextResponse.json(response.data.data);
  } catch (error: any) {
    return NextResponse.json(
      { detail: error.response?.data?.message || 'Failed to delete tier' },
      { status: error.response?.status || 500 }
    );
  }
}
