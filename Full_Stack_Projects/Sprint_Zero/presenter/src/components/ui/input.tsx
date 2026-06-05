import * as React from "react";
import { cn } from "@/lib/cn";

export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "h-10 w-full rounded-md border border-border bg-surface px-3 text-[14px] text-fg",
      "placeholder:text-fg-subtle",
      "transition-colors duration-150",
      "hover:border-border-strong",
      "focus-visible:outline-none focus-visible:border-accent focus-visible:ring-2 focus-visible:ring-accent/30",
      "disabled:opacity-50",
      className
    )}
    {...props}
  />
));
Input.displayName = "Input";

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "w-full rounded-md border border-border bg-surface px-3 py-2.5 text-[14px] text-fg leading-relaxed",
      "placeholder:text-fg-subtle",
      "transition-colors duration-150",
      "hover:border-border-strong",
      "focus-visible:outline-none focus-visible:border-accent focus-visible:ring-2 focus-visible:ring-accent/30",
      "resize-y min-h-[90px]",
      className
    )}
    {...props}
  />
));
Textarea.displayName = "Textarea";

export const Label = React.forwardRef<
  HTMLLabelElement,
  React.LabelHTMLAttributes<HTMLLabelElement>
>(({ className, ...props }, ref) => (
  <label
    ref={ref}
    className={cn("text-[13px] font-medium text-fg tracking-tight", className)}
    {...props}
  />
));
Label.displayName = "Label";

export function FieldHint({ children, className }: { children: React.ReactNode; className?: string }) {
  return <p className={cn("text-[12px] text-fg-subtle mt-1.5 leading-relaxed", className)}>{children}</p>;
}
