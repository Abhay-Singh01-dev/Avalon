import React from "react";
import { cn } from "@/lib/utils";

interface SelectContextValue {
  value: string;
  onValueChange: (value: string) => void;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const SelectContext = React.createContext<SelectContextValue | undefined>(
  undefined
);

export interface SelectProps {
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  children: React.ReactNode;
}

const Select = ({
  value,
  defaultValue = "",
  onValueChange,
  children,
}: SelectProps) => {
  const [internalValue, setInternalValue] = React.useState(defaultValue);
  const [open, setOpen] = React.useState(false);
  const activeValue = value !== undefined ? value : internalValue;

  const handleValueChange = (newValue: string) => {
    if (value === undefined) setInternalValue(newValue);
    onValueChange?.(newValue);
    setOpen(false);
  };

  return (
    <SelectContext.Provider
      value={{
        value: activeValue,
        onValueChange: handleValueChange,
        open,
        onOpenChange: setOpen,
      }}
    >
      <div className="relative inline-block w-full">{children}</div>
    </SelectContext.Provider>
  );
};

export interface SelectTriggerProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean;
}

const SelectTrigger = React.forwardRef<HTMLButtonElement, SelectTriggerProps>(
  ({ className, onClick, ...props }, ref) => {
    const context = React.useContext(SelectContext);

    return (
      <button
        className={cn(
          "flex h-10 w-full items-center justify-between rounded-md border border-gray-800 bg-black px-3 py-2 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        onClick={(e) => {
          context?.onOpenChange(!context?.open);
          onClick?.(e);
        }}
        {...props}
      />
    );
  }
);
SelectTrigger.displayName = "SelectTrigger";

export interface SelectValueProps
  extends React.HTMLAttributes<HTMLSpanElement> {
  placeholder?: string;
}

const SelectValue = ({
  placeholder = "Select...",
  className,
}: SelectValueProps) => {
  const context = React.useContext(SelectContext);
  const selectedItem = context ? findItemByValue(context.value) : null;

  return (
    <span className={className}>
      {selectedItem ? selectedItem.label : placeholder}
    </span>
  );
};
SelectValue.displayName = "SelectValue";

export interface SelectContentProps
  extends React.HTMLAttributes<HTMLDivElement> {}

const SelectContent = React.forwardRef<HTMLDivElement, SelectContentProps>(
  ({ className, ...props }, ref) => {
    const context = React.useContext(SelectContext);

    return context?.open ? (
      <div
        className={cn(
          "absolute z-50 mt-1 w-full rounded-md border border-gray-800 bg-gray-900 shadow-lg",
          className
        )}
        ref={ref}
        {...props}
      />
    ) : null;
  }
);
SelectContent.displayName = "SelectContent";

export interface SelectItemProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string;
  label?: string;
}

const SelectItem = React.forwardRef<HTMLDivElement, SelectItemProps>(
  ({ value, label, className, onClick, ...props }, ref) => {
    const context = React.useContext(SelectContext);

    return (
      <div
        className={cn(
          "px-2 py-1.5 text-sm cursor-pointer hover:bg-gray-800/50 transition-colors",
          context?.value === value && "bg-blue-600/20 text-blue-400",
          className
        )}
        ref={ref}
        onClick={(e) => {
          context?.onValueChange(value);
          onClick?.(e);
        }}
        {...props}
      >
        {label}
      </div>
    );
  }
);
SelectItem.displayName = "SelectItem";

function findItemByValue(value: string): { label: string } | null {
  return null;
}

export { Select, SelectTrigger, SelectValue, SelectContent, SelectItem };
