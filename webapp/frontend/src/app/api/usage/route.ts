import { NextResponse } from "next/server";
import { getValidToken } from "@/lib/auth-server";
import axios from "axios";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function GET() {
  const token = await getValidToken();
  if (!token) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  try {
    const res = await axios.get(`${API}/usage/breakdown`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return NextResponse.json(res.data);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.response?.data?.detail || "Failed to fetch usage breakdown" },
      { status: error.response?.status || 500 }
    );
  }
}
