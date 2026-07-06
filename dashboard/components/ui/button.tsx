import * as React from "react";
import { cn } from "../../lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "danger" | "ghost";
  size?: "sm" | "md" | "lg" | "icon";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => {
    return (
      <button
        className={cn(
          "inline-flex items-center justify-center rounded-lg font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 disabled:pointer-events-none disabled:opacity-50",
          {
            "bg-cyan-500 hover:bg-cyan-600 text-white": variant === "primary",
            "bg-slate-800 hover:bg-slate-700 text-white border border-[#1e294b]": variant === "secondary",
            "border border-slate-700 bg-transparent hover:bg-slate-800 text-slate-300 hover:text-white": variant === "outline",
            "bg-red-500 hover:bg-red-600 text-white": variant === "danger",
            "bg-transparent hover:bg-slate-800 text-slate-400 hover:text-white": variant === "ghost",
            "h-8 px-3 text-xs": size === "sm",
            "h-10 px-4 py-2 text-sm": size === "md",
            "h-12 px-6 text-base": size === "lg",
            "h-9 w-9 p-0": size === "icon",
          },
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button };
