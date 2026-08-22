import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { getValidToken } from "@/lib/auth-server";
import axios from "axios";

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function GET() {
  try {
    const token = await getValidToken();

    if (!token) {
      return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const response = await axios.get(`${apiUrl}/admin/tiers`, {
      headers: { Authorization: `Bearer ${token}` }
    });

    return NextResponse.json(response.data.data);
  } catch (error: any) {
    return NextResponse.json(
      { detail: error.response?.data?.message || 'Failed to fetch tiers' },
      { status: error.response?.status || 500 }
    );
  }
}

export async function POST(request: Request) {
  try {
    const token = await getValidToken();

    if (!token) {
      return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const body = await request.json();
    const response = await axios.post(`${apiUrl}/admin/tiers`, body, {
      headers: { Authorization: `Bearer ${token}` }
    });

    return NextResponse.json(response.data.data);
  } catch (error: any) {
    return NextResponse.json(
      { detail: error.response?.data?.message || 'Failed to create tier' },
      { status: error.response?.status || 500 }
    );
  }
}
