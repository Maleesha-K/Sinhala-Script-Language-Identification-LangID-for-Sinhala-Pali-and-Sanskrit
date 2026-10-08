/** Where a signed-in user belongs: admins work in the admin panel only. */
export function homePath(role: string | null | undefined): string {
  return role === "admin" ? "/admin" : "/dashboard";
}
