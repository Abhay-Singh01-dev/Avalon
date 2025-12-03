import React, { useRef } from "react";
import { Sparkles, Download } from "lucide-react";
import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import { Button } from "@/components/ui/button";

type MarkdownComponents = Components;

function StreamingMessageBubble({ message }: { message: string }) {
  const tableRef = useRef<HTMLDivElement>(null);

  // Remove the cursor character for markdown rendering
  const displayMessage = message.replace(/\|$/, "");
  const showCursor = message.endsWith("|");

  const extractTableAsCSV = () => {
    if (!tableRef.current) return;

    const tables = tableRef.current.querySelectorAll("table");
    if (tables.length === 0) return;

    // Convert first table to CSV
    const table = tables[0];
    const rows = Array.from(table.querySelectorAll("tr"));

    const csvContent = rows
      .map((row) => {
        const cells = Array.from(row.querySelectorAll("th, td"));
        return cells
          .map((cell) => {
            const text = cell.textContent || "";
            // Escape quotes and wrap in quotes if contains comma, quote, or newline
            if (
              text.includes(",") ||
              text.includes('"') ||
              text.includes("\n")
            ) {
              return '"' + text.replace(/"/g, '""') + '"';
            }
            return text;
          })
          .join(",");
      })
      .join("\n");

    // Download CSV
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", `table_${Date.now()}.csv`);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const hasTable =
    message.includes("|") && (message.match(/\|/g) || []).length > 2;

  const components: MarkdownComponents = {
    // Tables
    table: ({ node, children, ...props }) => (
      <div className="overflow-x-auto my-4">
        <table
          {...props}
          className="w-full border-collapse border border-gray-700"
          style={{ tableLayout: "auto" }}
        >
          {children}
        </table>
      </div>
    ),
    thead: ({ node, children, ...props }) => (
      <thead {...props} className="bg-gray-800/50">
        {children}
      </thead>
    ),
    tbody: ({ node, children, ...props }) => (
      <tbody {...props}>
        {children}
      </tbody>
    ),
    th: ({ node, children, ...props }) => (
      <th
        {...props}
        className="border border-gray-700 px-3 py-2.5 text-left font-semibold text-gray-200"
      >
        {children}
      </th>
    ),
    td: ({ node, children, ...props }) => (
      <td {...props} className="border border-gray-700 px-3 py-2.5 text-gray-300">
        {children}
      </td>
    ),
    tr: ({ node, children, ...props }) => (
      <tr {...props} className="hover:bg-gray-800/30 transition-colors">
        {children}
      </tr>
    ),
    // Lists - compact spacing
    ul: ({ node, children, ...props }) => (
      <ul {...props} className="list-disc pl-5 my-2 space-y-1">
        {children}
      </ul>
    ),
    ol: ({ node, children, ...props }) => (
      <ol {...props} className="list-decimal pl-5 my-2 space-y-1">
        {children}
      </ol>
    ),
    li: ({ node, ordered, index, depth, className, children, ...props }: any) => {
      // Remove unsupported props to avoid React warnings
      const { ordered: _, index: __, depth: ___, ...restProps } = props;
      return (
        <li {...restProps} className={`leading-normal ${className || ''}`}>
          {children}
        </li>
      );
    },
    // Paragraphs - tight spacing
    p: ({ node, children, ...props }) => (
      <p {...props} className="my-1.5 leading-normal">
        {children}
      </p>
    ),
    // Headings - consistent styling
    h1: ({ node, children, ...props }) => (
      <h1 {...props} className="text-2xl font-bold mt-6 mb-3 pb-2 border-b border-blue-500/30 text-gray-100">
        {children}
      </h1>
    ),
    h2: ({ node, children, ...props }) => (
      <h2 {...props} className="text-xl font-semibold mt-5 mb-3 pb-1.5 border-b border-gray-700/50 text-gray-100">
        {children}
      </h2>
    ),
    h3: ({ node, children, ...props }) => (
      <h3 {...props} className="text-lg font-medium mt-4 mb-2 text-gray-100">
        {children}
      </h3>
    ),
    h4: ({ node, children, ...props }) => (
      <h4 {...props} className="text-base font-medium mt-3 mb-2 text-gray-200">
        {children}
      </h4>
    ),
    // Text formatting
    strong: ({ node, children }) => (
      <strong className="font-semibold text-gray-50">
        {children}
      </strong>
    ),
    em: ({ node, children }) => (
      <em className="italic text-gray-300">
        {children}
      </em>
    ),
    // Code blocks
    code: ({ node, className, children, ...props }: any) => {
      // Type assertion for the inline prop since ReactMarkdown's type definitions might be incorrect
      const isInline = (props as any).inline;
      
      if (isInline) {
        const { inline: _, ...restProps } = props;
        return (
          <code
            className="bg-gray-800/80 text-amber-300 px-1.5 py-0.5 rounded text-sm font-mono"
            {...restProps}
          >
            {children}
          </code>
        );
      }
      
      // For block code
      return (
        <pre className="bg-gray-900/80 p-4 rounded-lg overflow-x-auto my-4 border border-gray-700/50">
          <code className={`text-sm font-mono text-gray-200 ${className || ''}`} {...props}>
            {children}
          </code>
        </pre>
      );
    },
    blockquote: ({ node, children, ...props }) => (
      <blockquote
        {...props}
        className="border-l-4 border-blue-500/50 pl-4 py-2 my-4 text-gray-400 italic bg-gray-900/30 rounded-r"
      >
        {children}
      </blockquote>
    ),
    a: ({ node, children, ...props }) => (
      <a
        {...props}
        className="text-blue-400 hover:text-blue-300 hover:underline transition-colors"
        target="_blank"
        rel="noopener noreferrer"
      >
        {children}
      </a>
    ),
    hr: ({ node, ...props }) => (
      <hr {...props} className="my-6 border-gray-700/50" />
    ),
  };

  return (
    <div
      className="flex gap-4 mb-6 justify-start"
      style={{ minHeight: "60px" }}
    >
      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 via-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/30 flex-shrink-0">
        <Sparkles className="w-5 h-5 text-white" />
      </div>

      <div
        className="max-w-3xl rounded-2xl px-5 py-4 bg-gray-900/50 border border-gray-800 text-gray-300 relative"
        style={{ minHeight: "40px", wordBreak: "break-word" }}
      >
        {hasTable && (
          <Button
            onClick={extractTableAsCSV}
            size="sm"
            variant="ghost"
            className="absolute top-2 right-2 z-10 bg-gray-800/80 hover:bg-gray-700 text-gray-300 hover:text-white"
            title="Download as CSV"
          >
            <Download className="w-4 h-4 mr-1" />
            CSV
          </Button>
        )}
        <div
          ref={tableRef}
          className="markdown-content max-w-none"
          style={{
            lineHeight: "1.6",
            minHeight: "1.5em",
            overflow: "hidden",
          }}
        >
          <ReactMarkdown
            components={components}
            remarkPlugins={[]}
          >
            {displayMessage}
          </ReactMarkdown>
          {showCursor && (
            <span className="inline-block w-0.5 h-5 bg-blue-400 ml-0.5 animate-pulse" />
          )}
        </div>
      </div>
    </div>
  );
}

export default React.memo(StreamingMessageBubble);
