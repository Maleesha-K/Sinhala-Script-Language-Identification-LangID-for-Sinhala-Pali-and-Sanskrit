import { cookies } from "next/headers";
import { isTokenStale, refreshTokens, setAuthCookies } from "@/lib/auth-tokens";

export { isTokenStale, refreshTokens, setAuthCookies } from "@/lib/auth-tokens";

/**
 * Gets a valid access token. If the current access token is missing or expired,
 * it attempts to use the refresh token to get new ones.
 * Updates cookies if refreshed (only possible in route handlers / actions).
 * Returns the access token, or null if unauthenticated.
 */
export async function getValidToken(): Promise<string | null> {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get("access_token")?.value;
  
  if (accessToken && !isTokenStale(accessToken)) {
    return accessToken;
  }

  const refreshToken = cookieStore.get("refresh_token")?.value;
  if (!refreshToken) return null;

  const tokens = await refreshTokens(refreshToken);
  if (!tokens) return null;

  try {
    setAuthCookies(cookieStore, tokens.access_token, tokens.refresh_token);
  } catch {
    // Server Components cannot set cookies; the token is still usable for this request.
  }
  return tokens.access_token;
}
