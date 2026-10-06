import { API_URL } from "@/lib/backend";

/**
 * PayHere IPN webhook. The backend's checkout params point `notify_url` here
 * (the public frontend origin), so relay the form post to FastAPI unchanged.
 */
export async function POST(request: Request) {
  const body = await request.text();
  try {
    const res = await fetch(`${API_URL}/payments/payhere/notify`, {
      method: "POST",
      headers: { "Content-Type": request.headers.get("content-type") ?? "application/x-www-form-urlencoded" },
      body,
    });
    return new Response(await res.text(), {
      status: res.status,
      headers: { "Content-Type": res.headers.get("content-type") ?? "text/plain" },
    });
  } catch {
    // A non-2xx makes PayHere retry the notification later.
    return new Response("Backend unavailable", { status: 502 });
  }
}
