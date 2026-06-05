import * as React from "react";
import { cn } from "@/lib/cn";

type Tone = "neutral" | "accent" | "success" | "warn" | "danger";

const toneClasses: Record<Tone, string> = {
  neutral: "bg-surface-3 text-fg-muted border-border",
  accent: "bg-accent/10 text-accent border-accent/30",
  success: "bg-success/10 text-success border-success/30",
  warn: "bg-warn/10 text-warn border-warn/30",
  danger: "bg-danger/10 text-danger border-danger/30",
};

export function Badge({
  tone = "neutral",
  className,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full",
        "text-[11px] font-medium tracking-wide uppercase border",
        toneClasses[tone],
        className
      )}
      {...props}
    />
  );
}

export function Dot({ tone = "neutral" }: { tone?: "neutral" | "accent" | "success" | "warn" | "danger" }) {
  const color = {
    neutral: "bg-fg-subtle",
    accent: "bg-accent",
    success: "bg-success",
    warn: "bg-warn",
    danger: "bg-danger",
  }[tone];
  return <span className={cn("inline-block w-1.5 h-1.5 rounded-full", color)} />;
}
