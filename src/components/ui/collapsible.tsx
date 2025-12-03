import * as React from "react";
import { cn } from "@/lib/utils";

// Context to pass open state without prop drilling
const CollapsibleContext = React.createContext<{
  open: boolean;
  onOpenChange: (open: boolean) => void;
} | null>(null);

const useCollapsible = () => {
  const context = React.useContext(CollapsibleContext);
  return context;
};

interface CollapsibleProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: React.ReactNode;
}

const Collapsible = React.forwardRef<
  HTMLDivElement, 
  CollapsibleProps & React.HTMLAttributes<HTMLDivElement>
>(({ open = false, onOpenChange = () => {}, children, ...props }, ref) => {
    return (
      <CollapsibleContext.Provider value={{ open, onOpenChange }}>
        <div ref={ref} {...props}>
          {children}
        </div>
      </CollapsibleContext.Provider>
    );
  }
);
Collapsible.displayName = "Collapsible";

interface CollapsibleTriggerProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean;
}

const CollapsibleTrigger = React.forwardRef<
  HTMLButtonElement,
  CollapsibleTriggerProps
>(({ className, asChild, children, ...props }, ref) => {
  const context = useCollapsible();
  
  return (
    <button
      ref={ref}
      type="button"
      onClick={() => context?.onOpenChange(!context.open)}
      className={cn(className)}
      {...props}
    >
      {children}
    </button>
  );
});
CollapsibleTrigger.displayName = "CollapsibleTrigger";

interface CollapsibleContentProps extends React.HTMLAttributes<HTMLDivElement> {}

const CollapsibleContent = React.forwardRef<
  HTMLDivElement,
  CollapsibleContentProps
>(({ className, children, ...props }, ref) => {
  const context = useCollapsible();
  
  if (!context?.open) return null;
  return (
    <div ref={ref} className={cn(className)} {...props}>
      {children}
    </div>
  );
});
CollapsibleContent.displayName = "CollapsibleContent";

export { Collapsible, CollapsibleTrigger, CollapsibleContent };
