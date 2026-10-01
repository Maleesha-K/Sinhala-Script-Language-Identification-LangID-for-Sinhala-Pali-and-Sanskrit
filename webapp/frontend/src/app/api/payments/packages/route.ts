import { NextResponse } from "next/server";
import axios from "axios";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function GET() {
  try {
    const res = await axios.get(`${API}/payments/packages`);
    return NextResponse.json(res.data);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.response?.data?.detail || "Failed to fetch packages" },
      { status: error.response?.status || 500 }
    );
  }
}
