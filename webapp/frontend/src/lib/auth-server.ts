import { cookies } from "next/headers";
import axios from "axios";

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

/**
 * Gets a valid access token. If the current access token is missing or expired,
 * it attempts to use the refresh token to get new ones.
 * Updates cookies if refreshed.
 * Returns the access token, or null if unauthenticated.
 */
export async function getValidToken(): Promise<string | null> {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get("access_token")?.value;
  
  if (accessToken) return accessToken;

  const refreshToken = cookieStore.get("refresh_token")?.value;
  if (!refreshToken) return null;

  try {
    const response = await axios.post(`${apiUrl}/auth/refresh`, {
      refresh_token: refreshToken
    });
    
    const newAccess = response.data.data.access_token;
    const newRefresh = response.data.data.refresh_token;

    cookieStore.set('access_token', newAccess, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      maxAge: 15 * 60, // 15 mins
    });

    cookieStore.set('refresh_token', newRefresh, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      maxAge: 7 * 24 * 60 * 60, // 7 days
    });

    return newAccess;
  } catch (e) {
    // If refresh fails (e.g. invalid refresh token), return null
    return null;
  }
}
