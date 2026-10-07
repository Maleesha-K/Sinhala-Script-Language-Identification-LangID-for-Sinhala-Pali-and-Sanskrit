import { NextResponse } from "next/server";
import axios, { type Method } from "axios";
import { getValidToken } from "@/lib/auth-server";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

/**
 * Pulls a readable message out of a failed backend call. The backend wraps
 * errors as `{ status, message, data }`; FastAPI's own errors use `detail`.
 */
export function backendErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;
    if (typeof data?.message === "string" && data.message) return data.message;
    if (typeof data?.detail === "string" && data.detail) return data.detail;
  }
  return fallback;
}

type ForwardOptions = {
  method?: Method;
  body?: unknown;
  params?: Record<string, string>;
  headers?: Record<string, string>;
  /** Return only the backend's `data` field instead of the whole envelope. */
  unwrap?: boolean;
  /** Set to false for public endpoints. */
  auth?: boolean;
  /** Message used when the backend gives none. */
  fallback: string;
};

/**
 * Forwards a request to the FastAPI backend with the user's access token.
 * Errors always come back as `{ detail }` with the backend's status code.
 */
export async function forward(path: string, options: ForwardOptions) {
  let token: string | null = null;
  if (options.auth !== false) {
    token = await getValidToken();
    if (!token) {
      return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }
  }

  try {
    const res = await axios.request({
      url: `${API_URL}${path}`,
      method: options.method ?? "GET",
      data: options.body,
      params: options.params,
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    });
    return NextResponse.json(options.unwrap ? res.data.data : res.data, { status: res.status });
  } catch (error) {
    const status = axios.isAxiosError(error) ? error.response?.status ?? 502 : 500;
    return NextResponse.json({ detail: backendErrorMessage(error, options.fallback) }, { status });
  }
}
