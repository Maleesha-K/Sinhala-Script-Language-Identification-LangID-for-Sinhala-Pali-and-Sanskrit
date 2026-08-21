import { NextResponse } from 'next/server';
import axios from 'axios';
import { cookies } from 'next/headers';

export async function GET() {
  const cookieStore = await cookies();
  const token = cookieStore.get('access_token')?.value;

  if (!token) {
    return NextResponse.json({ detail: 'Not authenticated' }, { status: 401 });
  }

  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    
    // Call the backend to get current user details
    const response = await axios.get(`${apiUrl}/users/me`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    return NextResponse.json(response.data.data);
  } catch (error: any) {
    // If access token is invalid/expired, we might want to try refreshing it, 
    // but for simplicity we'll just return 401 and let the client handle it.
    return NextResponse.json(
      { detail: error.response?.data?.message || error.response?.data?.detail || 'Not authenticated' },
      { status: error.response?.status || 401 }
    );
  }
}
