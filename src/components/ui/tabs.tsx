import React from "react";
import { cn } from "@/lib/utils";

interface TabsContextValue {
  value: string;
  onValueChange: (value: string) => void;
}

const TabsContext = React.createContext<TabsContextValue | undefined>(
  undefined
);

export interface TabsProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
}

const Tabs = React.forwardRef<HTMLDivElement, TabsProps>(
  (
    { className, value, defaultValue = "", onValueChange, children, ...props },
    ref
  ) => {
    const [internalValue, setInternalValue] = React.useState(defaultValue);
    const activeValue = value !== undefined ? value : internalValue;

    const handleValueChange = (newValue: string) => {
      if (value === undefined) setInternalValue(newValue);
      onValueChange?.(newValue);
    };

    return (
      <TabsContext.Provider
        value={{ value: activeValue, onValueChange: handleValueChange }}
      >
        <div className={cn("w-full", className)} ref={ref} {...props}>
          {children}
        </div>
      </TabsContext.Provider>
    );
  }
);
Tabs.displayName = "Tabs";

export interface TabsListProps extends React.HTMLAttributes<HTMLDivElement> {}

const TabsList = React.forwardRef<HTMLDivElement, TabsListProps>(
  ({ className, ...props }, ref) => (
    <div
      className={cn(
        "inline-flex items-center justify-center rounded-lg bg-gray-900 border border-gray-800 p-1",
        className
      )}
      ref={ref}
      {...props}
    />
  )
);
TabsList.displayName = "TabsList";

export interface TabsTriggerProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string;
}

const TabsTrigger = React.forwardRef<HTMLButtonElement, TabsTriggerProps>(
  ({ className, value, onClick, ...props }, ref) => {
    const context = React.useContext(TabsContext);

    return (
      <button
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50",
          context?.value === value
            ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
            : "text-gray-400 hover:text-gray-200",
          className
        )}
        ref={ref}
        onClick={(e) => {
          context?.onValueChange(value);
          onClick?.(e);
        }}
        {...props}
      />
    );
  }
);
TabsTrigger.displayName = "TabsTrigger";

export interface TabsContentProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string;
}

const TabsContent = React.forwardRef<HTMLDivElement, TabsContentProps>(
  ({ className, value, ...props }, ref) => {
    const context = React.useContext(TabsContext);
    return context?.value === value ? (
      <div
        className={cn(
          "mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          className
        )}
        ref={ref}
        {...props}
      />
    ) : null;
  }
);
TabsContent.displayName = "TabsContent";

export { Tabs, TabsList, TabsTrigger, TabsContent };
