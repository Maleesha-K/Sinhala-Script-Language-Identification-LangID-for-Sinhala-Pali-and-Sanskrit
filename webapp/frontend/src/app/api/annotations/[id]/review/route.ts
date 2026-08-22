import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { getValidToken } from "@/lib/auth-server";
import axios from "axios";

export async function PUT(request: Request, props: { params: Promise<{ id: string }> }) {
  const params = await props.params;
  const token = await getValidToken();
  const body = await request.json();

  try {
    const res = await axios.put(`http://localhost:8000/api/v1/annotations/${params.id}/review`, body, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return NextResponse.json(res.data);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: error.response?.status || 500 });
  }
}
