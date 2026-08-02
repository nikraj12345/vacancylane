import * as React from "react";
import { cn } from "@/lib/utils";

export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, type, ...props }, ref) => (
  <input
    type={type}
    className={cn(
      "flex h-9 w-full rounded-lg border border-white/10 bg-white/[0.045] px-3 py-1 text-sm text-slate-200 placeholder:text-slate-600 focus-visible:border-emerald-400/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/15 disabled:cursor-not-allowed disabled:opacity-50",
      className
    )}
    ref={ref}
    {...props}
  />
));
Input.displayName = "Input";
