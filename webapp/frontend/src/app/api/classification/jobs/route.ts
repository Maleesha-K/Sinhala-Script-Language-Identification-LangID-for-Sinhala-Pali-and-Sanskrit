import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { getValidToken } from "@/lib/auth-server";
import axios from "axios";

const API = "http://localhost:8000/api/v1";

export async function POST(request: Request) {
  const token = await getValidToken();
  if (!token) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const body = await request.json();
  try {
    const res = await axios.post(`${API}/classification/jobs`, body, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return NextResponse.json(res.data);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.response?.data?.detail || "Failed" },
      { status: error.response?.status || 500 }
    );
  }
}

export async function GET() {
  const token = await getValidToken();
  if (!token) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  try {
    const res = await axios.get(`${API}/classification/jobs`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return NextResponse.json(res.data);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.response?.data?.detail || "Failed" },
      { status: error.response?.status || 500 }
    );
  }
}
