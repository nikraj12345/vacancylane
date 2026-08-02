import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded-lg text-sm font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/40 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "bg-emerald-500 text-[#07100c] shadow-sm shadow-emerald-950/40 hover:bg-emerald-400",
        secondary: "bg-white/8 text-slate-200 hover:bg-white/12",
        ghost: "text-slate-300 hover:bg-white/6 hover:text-white",
        outline:
          "border border-white/10 bg-transparent text-slate-300 hover:border-white/20 hover:bg-white/5",
        danger: "bg-rose-600 text-white hover:bg-rose-500",
        success: "bg-emerald-500 text-[#07100c] hover:bg-emerald-400",
      },
      size: {
        default: "h-8 px-3 py-1",
        sm: "h-7 rounded px-2 text-xs",
        lg: "h-9 px-4",
        icon: "h-8 w-8",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
