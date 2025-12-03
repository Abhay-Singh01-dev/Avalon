import React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline";
}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = "default", ...props }, ref) => {
    const variants = {
      default: "bg-blue-500/20 text-blue-400 border-blue-500/30",
      secondary: "bg-gray-500/20 text-gray-400 border-gray-500/30",
      destructive: "bg-red-500/20 text-red-400 border-red-500/30",
      outline: "text-gray-400 border border-gray-800",
    };

    return (
      <div
        className={cn(
          "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
          variants[variant],
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Badge.displayName = "Badge";

export { Badge };
