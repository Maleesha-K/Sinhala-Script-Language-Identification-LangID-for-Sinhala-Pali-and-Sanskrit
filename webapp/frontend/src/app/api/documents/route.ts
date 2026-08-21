import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import axios from "axios";

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function GET() {
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get("access_token")?.value;

    if (!token) {
      return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const response = await axios.get(`${apiUrl}/documents`, {
      headers: { Authorization: `Bearer ${token}` }
    });

    return NextResponse.json(response.data.data);
  } catch (error: any) {
    return NextResponse.json(
      { detail: error.response?.data?.message || 'Failed to fetch documents' },
      { status: error.response?.status || 500 }
    );
  }
}

export async function POST(request: Request) {
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get("access_token")?.value;

    if (!token) {
      return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    // We must pass the raw form data directly to axios
    const formData = await request.formData();
    
    const response = await axios.post(`${apiUrl}/documents/upload`, formData, {
      headers: { 
        Authorization: `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    });

    return NextResponse.json(response.data.data);
  } catch (error: any) {
    return NextResponse.json(
      { detail: error.response?.data?.message || 'Failed to upload document' },
      { status: error.response?.status || 500 }
    );
  }
}
