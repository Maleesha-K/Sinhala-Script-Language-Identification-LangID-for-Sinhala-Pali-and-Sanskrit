import { forward } from "@/lib/backend";

export async function GET() {
  return forward("/users/me", { unwrap: true, fallback: "Not authenticated" });
}
