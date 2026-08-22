import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { getValidToken } from "@/lib/auth-server";
import axios from "axios";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const pendingOnly = searchParams.get("pending_only") || "true";
  const token = await getValidToken();

  try {
    const res = await axios.get(`http://localhost:8000/api/v1/annotations?pending_only=${pendingOnly}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return NextResponse.json(res.data);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: error.response?.status || 500 });
  }
}

export async function POST(request: Request) {
  const token = await getValidToken();
  const body = await request.json();

  try {
    const res = await axios.post(`http://localhost:8000/api/v1/annotations`, body, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return NextResponse.json(res.data);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: error.response?.status || 500 });
  }
}
