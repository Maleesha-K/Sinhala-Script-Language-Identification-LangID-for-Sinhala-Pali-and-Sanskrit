import { NextResponse } from "next/server";
import { getValidToken } from "@/lib/auth-server";

export async function GET() {
  const token = await getValidToken();
  
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }
  
  return NextResponse.json({ token });
}
