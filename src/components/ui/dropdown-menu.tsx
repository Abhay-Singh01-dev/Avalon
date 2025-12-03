import React from "react";
import { cn } from "@/lib/utils";

interface DropdownMenuContextValue {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const DropdownMenuContext = React.createContext<
  DropdownMenuContextValue | undefined
>(undefined);

export interface DropdownMenuProps {
  children: React.ReactNode;
}

const DropdownMenu = ({ children }: DropdownMenuProps) => {
  const [open, setOpen] = React.useState(false);

  return (
    <DropdownMenuContext.Provider value={{ open, onOpenChange: setOpen }}>
      <div className="relative inline-block text-left">{children}</div>
    </DropdownMenuContext.Provider>
  );
};

export interface DropdownMenuTriggerProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean;
}

const DropdownMenuTrigger = React.forwardRef<
  HTMLButtonElement,
  DropdownMenuTriggerProps
>(({ onClick, asChild, children, ...props }, ref) => {
  const context = React.useContext(DropdownMenuContext);

  const handleClick = (e: React.MouseEvent) => {
    context?.onOpenChange(!context?.open);
    onClick?.(e as any);
  };

  // When asChild is true, clone the child element and add the click handler
  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children as React.ReactElement<any>, {
      ref,
      onClick: (e: React.MouseEvent) => {
        handleClick(e);
        // Also call the child's onClick if it exists
        const childOnClick = (children as React.ReactElement<any>).props?.onClick;
        childOnClick?.(e);
      },
    });
  }

  return (
    <button
      ref={ref}
      onClick={handleClick}
      {...props}
    >
      {children}
    </button>
  );
});
DropdownMenuTrigger.displayName = "DropdownMenuTrigger";

export interface DropdownMenuContentProps
  extends React.HTMLAttributes<HTMLDivElement> {
  align?: "start" | "center" | "end";
}

const DropdownMenuContent = React.forwardRef<
  HTMLDivElement,
  DropdownMenuContentProps
>(({ className, align = "start", ...props }, ref) => {
  const context = React.useContext(DropdownMenuContext);
  const contentRef = React.useRef<HTMLDivElement>(null);

  // Close on click outside
  React.useEffect(() => {
    if (!context?.open) return;
    
    const handleClickOutside = (e: MouseEvent) => {
      if (contentRef.current && !contentRef.current.contains(e.target as Node)) {
        context?.onOpenChange(false);
      }
    };
    
    // Add slight delay to prevent immediate close
    const timer = setTimeout(() => {
      document.addEventListener('click', handleClickOutside);
    }, 10);
    
    return () => {
      clearTimeout(timer);
      document.removeEventListener('click', handleClickOutside);
    };
  }, [context?.open]);

  return context?.open ? (
    <div
      className={cn(
        "absolute mt-2 min-w-[180px] rounded-lg border border-gray-700 bg-gray-900 shadow-xl z-[100] py-1 backdrop-blur-sm",
        align === "end" && "right-0",
        align === "start" && "left-0",
        align === "center" && "left-1/2 -translate-x-1/2",
        className
      )}
      ref={(node) => {
        (contentRef as any).current = node;
        if (typeof ref === 'function') ref(node);
        else if (ref) ref.current = node;
      }}
      {...props}
    />
  ) : null;
});
DropdownMenuContent.displayName = "DropdownMenuContent";

export interface DropdownMenuItemProps
  extends React.HTMLAttributes<HTMLDivElement> {}

const DropdownMenuItem = React.forwardRef<
  HTMLDivElement,
  DropdownMenuItemProps
>(({ className, onClick, ...props }, ref) => {
  const context = React.useContext(DropdownMenuContext);

  return (
    <div
      className={cn(
        "flex items-center gap-2 px-3 py-2 text-sm text-gray-200 cursor-pointer hover:bg-gray-800 transition-colors rounded-md mx-1",
        className
      )}
      ref={ref}
      onClick={(e) => {
        e.stopPropagation();
        context?.onOpenChange(false);
        onClick?.(e);
      }}
      {...props}
    />
  );
});
DropdownMenuItem.displayName = "DropdownMenuItem";

export interface DropdownMenuLabelProps
  extends React.HTMLAttributes<HTMLDivElement> {}

const DropdownMenuLabel = React.forwardRef<
  HTMLDivElement,
  DropdownMenuLabelProps
>(({ className, ...props }, ref) => (
  <div
    className={cn("px-2 py-1.5 text-sm font-semibold text-gray-300", className)}
    ref={ref}
    {...props}
  />
));
DropdownMenuLabel.displayName = "DropdownMenuLabel";

export interface DropdownMenuSeparatorProps
  extends React.HTMLAttributes<HTMLHRElement> {}

const DropdownMenuSeparator = React.forwardRef<
  HTMLHRElement,
  DropdownMenuSeparatorProps
>(({ className, ...props }, ref) => (
  <hr
    className={cn("my-1 border-gray-800", className)}
    ref={ref as any}
    {...props}
  />
));
DropdownMenuSeparator.displayName = "DropdownMenuSeparator";

const DropdownMenuSubContext = React.createContext<{
  open: boolean;
  onOpenChange: (open: boolean) => void;
} | null>(null);

export interface DropdownMenuSubProps {
  children: React.ReactNode;
}

const DropdownMenuSub = ({ children }: DropdownMenuSubProps) => {
  const [open, setOpen] = React.useState(false);
  return (
    <DropdownMenuSubContext.Provider value={{ open, onOpenChange: setOpen }}>
      {children}
    </DropdownMenuSubContext.Provider>
  );
};

export interface DropdownMenuSubTriggerProps
  extends React.HTMLAttributes<HTMLDivElement> {}

const DropdownMenuSubTrigger = React.forwardRef<
  HTMLDivElement,
  DropdownMenuSubTriggerProps
>(({ className, children, ...props }, ref) => {
  const context = React.useContext(DropdownMenuSubContext);
  return (
    <div
      ref={ref}
      className={cn(
        "relative flex items-center gap-2 px-3 py-2 text-sm text-gray-200 cursor-pointer hover:bg-gray-800 transition-colors rounded-md mx-1",
        className
      )}
      onMouseEnter={() => context?.onOpenChange(true)}
      onMouseLeave={() => context?.onOpenChange(false)}
      {...props}
    >
      {children}
      <svg className="w-4 h-4 ml-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
      </svg>
    </div>
  );
});
DropdownMenuSubTrigger.displayName = "DropdownMenuSubTrigger";

export interface DropdownMenuSubContentProps
  extends React.HTMLAttributes<HTMLDivElement> {}

const DropdownMenuSubContent = React.forwardRef<
  HTMLDivElement,
  DropdownMenuSubContentProps
>(({ className, ...props }, ref) => {
  const context = React.useContext(DropdownMenuSubContext);
  return context?.open ? (
    <div
      ref={ref}
      className={cn(
        "absolute left-full top-0 ml-1 min-w-[160px] rounded-lg border border-gray-700 bg-gray-900 shadow-xl z-[100] py-1",
        className
      )}
      onMouseEnter={() => context?.onOpenChange(true)}
      onMouseLeave={() => context?.onOpenChange(false)}
      {...props}
    />
  ) : null;
});
DropdownMenuSubContent.displayName = "DropdownMenuSubContent";

export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
};
