import axios from "axios";

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const ACCESS_TOKEN_MAX_AGE = 15 * 60; // 15 mins, matches the backend
export const REFRESH_TOKEN_MAX_AGE = 7 * 24 * 60 * 60; // 7 days

type CookieWriter = { set: (name: string, value: string, options: Record<string, unknown>) => unknown };

/** Stores the backend's tokens as httpOnly cookies. */
export function setAuthCookies(store: CookieWriter, accessToken: string, refreshToken: string) {
  const base = {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
  };
  store.set("access_token", accessToken, { ...base, maxAge: ACCESS_TOKEN_MAX_AGE });
  store.set("refresh_token", refreshToken, { ...base, maxAge: REFRESH_TOKEN_MAX_AGE });
}

/** True when the JWT is missing, unreadable, or expires within 30 seconds. */
export function isTokenStale(token: string | undefined): boolean {
  if (!token) return true;
  try {
    const payload = JSON.parse(Buffer.from(token.split(".")[1], "base64").toString("utf-8"));
    return !(payload.exp && payload.exp * 1000 > Date.now() + 30000);
  } catch {
    return true;
  }
}

/** Exchanges a refresh token for a new token pair, or null if it is rejected. */
export async function refreshTokens(refreshToken: string): Promise<{ access_token: string; refresh_token: string } | null> {
  try {
    const response = await axios.post(`${apiUrl}/auth/refresh`, { refresh_token: refreshToken });
    return response.data.data;
  } catch {
    return null;
  }
}
