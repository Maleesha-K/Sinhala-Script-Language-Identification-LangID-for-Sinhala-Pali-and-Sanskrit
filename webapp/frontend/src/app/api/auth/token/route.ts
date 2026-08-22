import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { getValidToken } from "@/lib/auth-server";

export async function GET() {
  const token = await getValidToken();
  
  if (!token) {
    return NextResponse.json({ error: "No token" }, { status: 401 });
  }
  
  return NextResponse.json({ token });
}
