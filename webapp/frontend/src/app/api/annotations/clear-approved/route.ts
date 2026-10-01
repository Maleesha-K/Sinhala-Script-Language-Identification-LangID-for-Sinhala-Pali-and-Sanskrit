import { NextResponse } from "next/server";
import { getValidToken } from "@/lib/auth-server";
import axios from "axios";

export async function POST(request: Request) {
  const token = await getValidToken();
  const body = await request.json();

  try {
    const res = await axios.post(`http://localhost:8000/api/v1/annotations/clear-approved`, body, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return NextResponse.json(res.data);
  } catch (error: unknown) {
    const status = axios.isAxiosError(error) ? error.response?.status : undefined;
    const message = error instanceof Error ? error.message : "Request failed";
    return NextResponse.json({ error: message }, { status: status || 500 });
  }
}
