import Image, { type StaticImageData } from "next/image";
import { cn } from "@/lib/utils";

/** A product screenshot in a light browser frame. */
export function Screenshot({
  src,
  alt,
  url = "LangID",
  sizes = "(min-width: 1024px) 50vw, 100vw",
  preload,
  className,
}: {
  src: StaticImageData;
  alt: string;
  /** Page name shown in the frame's address bar. */
  url?: string;
  sizes?: string;
  preload?: boolean;
  className?: string;
}) {
  return (
    <figure
      className={cn(
        "overflow-hidden rounded-xl border border-slate-200 bg-white shadow-[0_24px_60px_-20px_rgba(30,64,175,0.35)] ring-1 ring-slate-900/5",
        className,
      )}
    >
      <div className="flex items-center gap-2 border-b border-slate-200 bg-slate-50 px-3 py-2" aria-hidden>
        <span className="h-2.5 w-2.5 rounded-full bg-slate-300" />
        <span className="h-2.5 w-2.5 rounded-full bg-slate-300" />
        <span className="h-2.5 w-2.5 rounded-full bg-slate-300" />
        <span className="ml-3 hidden truncate rounded-md bg-white px-3 py-0.5 text-[11px] text-slate-500 ring-1 ring-slate-200 sm:block">
          {url}
        </span>
      </div>
      <Image
        src={src}
        alt={alt}
        sizes={sizes}
        placeholder="blur"
        preload={preload}
        className="h-auto w-full"
      />
    </figure>
  );
}
