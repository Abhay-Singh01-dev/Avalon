import React from "react";
import { cn } from "@/lib/utils";

export interface TableProps extends React.HTMLAttributes<HTMLTableElement> {}

const Table = React.forwardRef<HTMLTableElement, TableProps>(
  ({ className, ...props }, ref) => (
    <div className="w-full overflow-auto">
      <table
        className={cn("w-full caption-bottom text-sm", className)}
        ref={ref}
        {...props}
      />
    </div>
  )
);
Table.displayName = "Table";

export interface TableHeaderProps
  extends React.HTMLAttributes<HTMLTableSectionElement> {}

const TableHeader = React.forwardRef<HTMLTableSectionElement, TableHeaderProps>(
  ({ className, ...props }, ref) => (
    <thead
      className={cn("border-b border-gray-800 bg-gray-800/50", className)}
      ref={ref}
      {...props}
    />
  )
);
TableHeader.displayName = "TableHeader";

export interface TableBodyProps
  extends React.HTMLAttributes<HTMLTableSectionElement> {}

const TableBody = React.forwardRef<HTMLTableSectionElement, TableBodyProps>(
  ({ className, ...props }, ref) => (
    <tbody
      className={cn("[&_tr:last-child]:border-0", className)}
      ref={ref}
      {...props}
    />
  )
);
TableBody.displayName = "TableBody";

export interface TableFooterProps
  extends React.HTMLAttributes<HTMLTableSectionElement> {}

const TableFooter = React.forwardRef<HTMLTableSectionElement, TableFooterProps>(
  ({ className, ...props }, ref) => (
    <tfoot
      className={cn(
        "border-t border-gray-800 bg-gray-900 font-medium",
        className
      )}
      ref={ref}
      {...props}
    />
  )
);
TableFooter.displayName = "TableFooter";

export interface TableRowProps
  extends React.HTMLAttributes<HTMLTableRowElement> {}

const TableRow = React.forwardRef<HTMLTableRowElement, TableRowProps>(
  ({ className, ...props }, ref) => (
    <tr
      className={cn(
        "border-b border-gray-800 transition-colors hover:bg-gray-800/30",
        className
      )}
      ref={ref}
      {...props}
    />
  )
);
TableRow.displayName = "TableRow";

export interface TableHeadProps
  extends React.ThHTMLAttributes<HTMLTableCellElement> {}

const TableHead = React.forwardRef<HTMLTableCellElement, TableHeadProps>(
  ({ className, ...props }, ref) => (
    <th
      className={cn(
        "h-12 px-4 text-left align-middle font-medium text-gray-400",
        className
      )}
      ref={ref}
      {...props}
    />
  )
);
TableHead.displayName = "TableHead";

export interface TableCellProps
  extends React.TdHTMLAttributes<HTMLTableCellElement> {}

const TableCell = React.forwardRef<HTMLTableCellElement, TableCellProps>(
  ({ className, ...props }, ref) => (
    <td
      className={cn("p-4 align-middle text-gray-400", className)}
      ref={ref}
      {...props}
    />
  )
);
TableCell.displayName = "TableCell";

export interface TableCaptionProps
  extends React.HTMLAttributes<HTMLTableCaptionElement> {}

const TableCaption = React.forwardRef<
  HTMLTableCaptionElement,
  TableCaptionProps
>(({ className, ...props }, ref) => (
  <caption
    className={cn("mt-4 text-sm text-gray-500", className)}
    ref={ref}
    {...props}
  />
));
TableCaption.displayName = "TableCaption";

export {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableHead,
  TableRow,
  TableCell,
  TableCaption,
};
