import React, { useRef } from "react";
import { User, Sparkles, Download, FileText, File } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Button } from "@/components/ui/button";

interface AttachedFile {
  id: string;
  name: string;
  size?: number;
}

interface MessageBubbleProps {
  message: string;
  isUser: boolean;
  attachedFiles?: AttachedFile[];
}

function MessageBubble({ message, isUser, attachedFiles = [] }: MessageBubbleProps) {
  const tableRef = useRef<HTMLDivElement>(null);

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
    !isUser && message.includes("|") && (message.match(/\|/g) || []).length > 2;

  return (
    <div
      className={`flex gap-4 mb-6 ${isUser ? "justify-end" : "justify-start"}`}
    >
      {!isUser && (
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 via-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/30 flex-shrink-0">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
      )}

      <div
        className={`max-w-3xl rounded-2xl px-5 py-4 ${
          isUser
            ? "bg-blue-600/10 border border-blue-500/30 text-gray-200"
            : "bg-gray-900/50 border border-gray-800 text-gray-300"
        }`}
        style={{ wordBreak: "break-word" }}
      >
        {isUser ? (
          <div>
            {/* Attached Files - ChatGPT style */}
            {attachedFiles && attachedFiles.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-3">
                {attachedFiles.map((file) => (
                  <div
                    key={file.id}
                    className="flex items-center gap-2 px-3 py-2 bg-gray-800/60 border border-gray-700 rounded-lg"
                  >
                    <div className="w-8 h-8 bg-gradient-to-br from-amber-500 to-orange-600 rounded-lg flex items-center justify-center">
                      <FileText className="w-4 h-4 text-white" />
                    </div>
                    <div className="flex flex-col">
                      <span className="text-sm text-gray-200 font-medium truncate max-w-[200px]">
                        {file.name}
                      </span>
                      {file.size && (
                        <span className="text-xs text-gray-500">
                          {(file.size / 1024).toFixed(1)} KB
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {message}
            </p>
          </div>
        ) : (
          <div className="relative">
            {hasTable && (
              <Button
                onClick={extractTableAsCSV}
                size="sm"
                variant="ghost"
                className="absolute top-0 right-0 z-10 bg-gray-800/80 hover:bg-gray-700 text-gray-300 hover:text-white"
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
                overflow: "hidden",
              }}
            >
              <ReactMarkdown
                components={{
                  // Tables
                  table: ({ node, ...props }) => (
                    <div className="overflow-x-auto my-4">
                      <table
                        {...props}
                        className="border-collapse border border-gray-700 w-full"
                        style={{ tableLayout: "auto" }}
                      />
                    </div>
                  ),
                  th: ({ node, ...props }) => (
                    <th
                      {...props}
                      className="border border-gray-700 px-3 py-2.5 bg-gray-800/60 text-left font-semibold text-gray-200"
                    />
                  ),
                  td: ({ node, ...props }) => (
                    <td
                      {...props}
                      className="border border-gray-700 px-3 py-2.5"
                    />
                  ),
                  tr: ({ node, ...props }) => (
                    <tr {...props} className="hover:bg-gray-800/30 transition-colors" />
                  ),

                  // Lists - compact spacing
                  ul: ({ node, ...props }) => (
                    <ul {...props} className="list-disc pl-5 my-2 space-y-1" />
                  ),
                  ol: ({ node, ...props }) => (
                    <ol {...props} className="list-decimal pl-5 my-2 space-y-1" />
                  ),
                  li: ({ node, children, ...props }) => (
                    <li {...props} className="leading-normal [&>p]:mb-0 [&>p]:mt-0">
                      {children}
                    </li>
                  ),

                  // Paragraphs - tight spacing
                  p: ({ node, ...props }) => (
                    <p {...props} className="my-1.5 leading-normal" />
                  ),

                  // Headings - consistent styling
                  h1: ({ node, ...props }) => (
                    <h1 {...props} className="text-2xl font-bold mt-6 mb-3 pb-2 border-b border-blue-500/30 text-gray-100" />
                  ),
                  h2: ({ node, ...props }) => (
                    <h2 {...props} className="text-xl font-semibold mt-5 mb-3 pb-1.5 border-b border-gray-700/50 text-gray-100" />
                  ),
                  h3: ({ node, ...props }) => (
                    <h3 {...props} className="text-lg font-medium mt-4 mb-2 text-gray-100" />
                  ),
                  h4: ({ node, ...props }) => (
                    <h4 {...props} className="text-base font-medium mt-3 mb-2 text-gray-200" />
                  ),

                  // Text formatting
                  strong: ({ node, ...props }) => (
                    <strong
                      {...props}
                      className="font-semibold text-gray-50"
                    />
                  ),
                  em: ({ node, ...props }) => (
                    <em {...props} className="italic text-gray-300" />
                  ),

                  // Code blocks
                  code: ({ node, className, ...props }) => {
                    const isInline = !className?.includes("language-");
                    return isInline ? (
                      <code
                        {...props}
                        className="bg-gray-800/80 px-1.5 py-0.5 rounded text-amber-300 text-sm font-mono"
                      />
                    ) : (
                      <code
                        {...props}
                        className="block bg-gray-900/80 p-4 rounded-lg my-4 text-gray-200 text-sm font-mono border border-gray-700/50"
                      />
                    );
                  },

                  // Blockquotes
                  blockquote: ({ node, ...props }) => (
                    <blockquote
                      {...props}
                      className="border-l-4 border-blue-500/50 pl-4 py-2 my-4 text-gray-400 italic bg-gray-900/30 rounded-r"
                    />
                  ),

                  // Links
                  a: ({ node, ...props }) => (
                    <a
                      {...props}
                      className="text-blue-400 hover:text-blue-300 hover:underline transition-colors"
                      target="_blank"
                      rel="noopener noreferrer"
                    />
                  ),

                  // Horizontal rule
                  hr: ({ node, ...props }) => (
                    <hr {...props} className="my-6 border-gray-700/50" />
                  ),
                }}
              >
                {message}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-gray-700 to-gray-800 flex items-center justify-center border border-gray-700 flex-shrink-0">
          <User className="w-5 h-5 text-gray-400" />
        </div>
      )}
    </div>
  );
}

export default React.memo(MessageBubble);
