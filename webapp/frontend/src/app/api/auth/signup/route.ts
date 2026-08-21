import { NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

    // Call the backend FastAPI signup route
    const response = await axios.post(`${apiUrl}/auth/signup`, body);
    
    // Automatically log in the user after signup by calling the local login API
    const loginResponse = await axios.post(`${process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'}/api/auth/login`, {
      email: body.email,
      password: body.password
    });

    return NextResponse.json({ success: true, user: response.data.data });
  } catch (error: any) {
    return NextResponse.json(
      { detail: error.response?.data?.message || error.response?.data?.detail || 'Signup failed' },
      { status: error.response?.status || 400 }
    );
  }
}
