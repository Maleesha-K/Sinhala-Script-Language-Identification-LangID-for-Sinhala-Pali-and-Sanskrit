import { NextResponse } from 'next/server';
import axios from 'axios';
import { cookies } from 'next/headers';
import { setAuthCookies } from "@/lib/auth-server";
import { API_URL, backendErrorMessage } from "@/lib/backend";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    // Call the backend FastAPI login route
    const response = await axios.post(`${API_URL}/auth/login`, body);
    
    // Extract tokens from the standard response wrapper
    const { access_token, refresh_token } = response.data.data;
    setAuthCookies(await cookies(), access_token, refresh_token);

    // The page sends admins to the admin panel and everyone else to the dashboard.
    const me = await axios.get(`${API_URL}/users/me`, {
      headers: { Authorization: `Bearer ${access_token}` },
    });

    return NextResponse.json({ success: true, role: me.data.data.role });
  } catch (error) {
    return NextResponse.json(
      { detail: backendErrorMessage(error, 'Authentication failed') },
      { status: axios.isAxiosError(error) ? error.response?.status ?? 401 : 401 }
    );
  }
}
