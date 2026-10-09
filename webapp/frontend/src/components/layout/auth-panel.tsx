import Image from "next/image";
import { Logo } from "@/components/layout/logo";

/** The blue left half of the login and signup pages: logo, illustration, caption. */
export function AuthPanel({ children }: { children: React.ReactNode }) {
  return (
    // Window-high, so the illustration has a definite space to fit into.
    <div className="hidden lg:flex w-1/2 h-screen sticky top-0 bg-primary flex-col justify-between gap-8 p-12">
      <Logo priority labelClassName="text-white" />
      <div className="relative flex-1 min-h-0">
        {/* The whole image, scaled down to fit and centered; its corners are rounded, not the space's. */}
        <Image
          src="/auth-illustration.jpg"
          alt=""
          width={1200}
          height={1789}
          priority
          sizes="50vw"
          className="absolute inset-0 m-auto h-auto w-auto max-h-full max-w-full rounded-3xl shadow-2xl shadow-black/20 ring-1 ring-white/20"
        />
      </div>
      <div>{children}</div>
    </div>
  );
}
