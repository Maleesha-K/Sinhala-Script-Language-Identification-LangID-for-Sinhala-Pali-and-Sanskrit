import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { getValidToken } from "@/lib/auth-server";
import axios from "axios";

const API = "http://localhost:8000/api/v1";

export async function GET(
  _request: Request,
  props: { params: Promise<{ id: string }> }
) {
  const params = await props.params;
  const token = await getValidToken();
  if (!token) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  try {
    const res = await axios.get(`${API}/classification/jobs/${params.id}`, {
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
