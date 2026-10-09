import Image from "next/image";
import { cn } from "@/lib/utils";

/** The LangID mark, optionally with the wordmark beside it. */
export function Logo({
  size = 32,
  label = "LangID",
  className,
  labelClassName,
  priority,
}: {
  size?: number;
  /** The wordmark; null shows the mark alone. */
  label?: string | null;
  className?: string;
  labelClassName?: string;
  priority?: boolean;
}) {
  return (
    <span className={cn("flex items-center gap-2", className)}>
      <Image
        src="/logo.png"
        alt={label ? "" : "LangID"}
        width={size}
        height={size}
        priority={priority}
        className="shrink-0 drop-shadow-sm"
      />
      {label && <span className={cn("font-bold text-lg tracking-tight text-foreground", labelClassName)}>{label}</span>}
    </span>
  );
}
