import * as React from "react";
import { cn } from "@/lib/utils";

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    className={cn(
      "flex min-h-[80px] w-full rounded-lg border border-white/10 bg-white/[0.035] px-3 py-2 font-mono text-sm text-slate-200 placeholder:text-slate-600 focus-visible:border-emerald-400/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/15 disabled:cursor-not-allowed disabled:opacity-50",
      className
    )}
    ref={ref}
    {...props}
  />
));
Textarea.displayName = "Textarea";
