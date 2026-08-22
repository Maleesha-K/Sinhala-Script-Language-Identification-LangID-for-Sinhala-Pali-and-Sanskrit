import { NextResponse } from "next/server";
import { cookies } from "next/headers";

export async function GET() {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  
  if (!token) {
    return NextResponse.json({ error: "No token" }, { status: 401 });
  }
  
  return NextResponse.json({ token });
}
