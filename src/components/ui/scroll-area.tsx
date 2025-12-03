import React from "react";
import { cn } from "@/lib/utils";

export interface ScrollAreaProps extends React.HTMLAttributes<HTMLDivElement> {}

const ScrollArea = React.forwardRef<HTMLDivElement, ScrollAreaProps>(
  ({ className, ...props }, ref) => (
    <div
      className={cn("relative overflow-y-auto thin-scrollbar", className)}
      ref={ref}
      {...props}
    />
  )
);
ScrollArea.displayName = "ScrollArea";

export { ScrollArea };
