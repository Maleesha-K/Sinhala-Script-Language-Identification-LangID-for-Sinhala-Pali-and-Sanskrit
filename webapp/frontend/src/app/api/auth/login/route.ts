import { NextResponse } from 'next/server';
import axios from 'axios';
import { cookies } from 'next/headers';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

    // Call the backend FastAPI login route
    const response = await axios.post(`${apiUrl}/auth/login`, body);
    
    // Extract tokens from the standard response wrapper
    const { access_token, refresh_token } = response.data.data;
    
    const cookieStore = await cookies();
    cookieStore.set('access_token', access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      maxAge: 15 * 60, // 15 minutes
    });

    cookieStore.set('refresh_token', refresh_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      maxAge: 7 * 24 * 60 * 60, // 7 days
    });

    return NextResponse.json({ success: true });
  } catch (error: any) {
    return NextResponse.json(
      { detail: error.response?.data?.message || error.response?.data?.detail || 'Authentication failed' },
      { status: error.response?.status || 401 }
    );
  }
}
