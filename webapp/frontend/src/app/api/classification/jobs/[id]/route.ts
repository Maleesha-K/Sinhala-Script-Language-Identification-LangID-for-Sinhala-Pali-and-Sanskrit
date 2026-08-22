import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import axios from "axios";

const API = "http://localhost:8000/api/v1";

export async function GET(
  _request: Request,
  props: { params: Promise<{ id: string }> }
) {
  const params = await props.params;
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
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
