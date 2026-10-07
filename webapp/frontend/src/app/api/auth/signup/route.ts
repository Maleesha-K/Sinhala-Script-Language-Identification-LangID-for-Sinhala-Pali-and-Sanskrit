import { NextResponse } from 'next/server';
import axios from 'axios';
import { cookies } from 'next/headers';
import { setAuthCookies } from "@/lib/auth-server";
import { API_URL, backendErrorMessage } from "@/lib/backend";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    // Call the backend FastAPI signup route
    const response = await axios.post(`${API_URL}/auth/signup`, body);
    
    // Log the new user in. This must set the cookies on *this* response: a
    // server-side call to /api/auth/login would set them on a response the
    // browser never sees.
    const login = await axios.post(`${API_URL}/auth/login`, {
      email: body.email,
      password: body.password,
    });
    const { access_token, refresh_token } = login.data.data;
    setAuthCookies(await cookies(), access_token, refresh_token);

    return NextResponse.json({ success: true, user: response.data.data });
  } catch (error) {
    return NextResponse.json(
      { detail: backendErrorMessage(error, 'Signup failed') },
      { status: axios.isAxiosError(error) ? error.response?.status ?? 400 : 400 }
    );
  }
}
