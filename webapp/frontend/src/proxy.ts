import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { isTokenStale, refreshTokens, setAuthCookies } from "@/lib/auth-tokens";

/**
 * Keeps the session alive on protected pages. The access token cookie lives
 * 15 minutes, and Server Component layouts cannot write cookies, so the
 * refresh has to happen here, before the page renders.
 */
export async function proxy(request: NextRequest) {
  const accessToken = request.cookies.get("access_token")?.value;
  if (!isTokenStale(accessToken)) return NextResponse.next();

  const refreshToken = request.cookies.get("refresh_token")?.value;
  const tokens = refreshToken ? await refreshTokens(refreshToken) : null;

  if (!tokens) {
    const response = NextResponse.redirect(new URL("/auth/login", request.url));
    response.cookies.delete("access_token");
    response.cookies.delete("refresh_token");
    return response;
  }

  // Forward the new tokens to this render, and to the browser for later ones.
  request.cookies.set("access_token", tokens.access_token);
  request.cookies.set("refresh_token", tokens.refresh_token);
  const response = NextResponse.next({ request: { headers: request.headers } });
  setAuthCookies(response.cookies, tokens.access_token, tokens.refresh_token);
  return response;
}

export const config = {
  matcher: ["/dashboard/:path*", "/admin/:path*"],
};
