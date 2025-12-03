import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { FileSpreadsheet, Download, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAppContext } from "@/context/AppContext";
import { api } from "@/lib/api";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export default function CsvViewerModal() {
  const { modals, setModalState, reports } = useAppContext();
  const [loading, setLoading] = React.useState(false);
  const [csvData, setCsvData] = React.useState<string | null>(null);
  const [title, setTitle] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);

  const isOpen = !!modals.csv?.reportId;
  const reportId = modals.csv?.reportId;

  // Helper to construct absolute URL for static files
  const getStaticFileUrl = (path: string): string => {
    if (path.startsWith("http")) return path;
    
    // For generated reports (from backend), use backend URL
    if (path.startsWith("/uploads/")) {
      return `${BASE_URL}${path}`;
    }
    
    // For mock reports in public folder, use frontend URL
    if (path.startsWith("/mock_reports/") || path.startsWith("/")) {
      return `${window.location.origin}${path}`;
    }
    
    return `${BASE_URL}${path}`;
  };

  // Helper to validate CSV content (not HTML)
  const isValidCsvContent = (text: string): boolean => {
    // Check if content looks like HTML
    const trimmed = text.trim().toLowerCase();
    if (
      trimmed.startsWith("<!doctype") ||
      trimmed.startsWith("<html") ||
      trimmed.startsWith("<head")
    ) {
      return false;
    }
    // Basic CSV validation: should have commas and multiple lines
    return text.includes(",") || text.includes("\n");
  };

  React.useEffect(() => {
    if (reportId) {
      setError(null);
      setLoading(true);

      // First check if fileUrl and title are provided in modal state (for mock reports)
      const modalFileUrl = modals.csv?.fileUrl;
      const modalTitle = modals.csv?.title;

      const fetchCsv = async (url: string) => {
        try {
          // Construct proper URL based on file location
          const fullUrl = url.startsWith("/uploads/")
            ? `${BASE_URL}${url}` // Backend generated reports
            : url.startsWith("http")
            ? url // Already absolute
            : `${window.location.origin}${url}`; // Mock reports in public/

          console.log('[CSV] Fetching:', fullUrl);
          // Force fresh fetch - bypass cache completely
          const response = await fetch(fullUrl, {
            cache: 'no-store',
            headers: {
              'Cache-Control': 'no-cache, no-store, must-revalidate',
              'Pragma': 'no-cache',
              'Expires': '0'
            }
          });
          console.log('[CSV] Response status:', response.status);
          const contentType = response.headers.get("content-type") || "";
          console.log("[CSV] Content-Type:", contentType);

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const text = await response.text();
          console.log("[CSV] Text length:", text.length);
          console.log("[CSV] First 100 chars:", text.substring(0, 100));

          // Validate we got some content
          if (!text || text.trim().length === 0) {
            throw new Error("CSV file is empty");
          }

          console.log("[CSV] ✓ CSV content loaded successfully");
          setCsvData(text);
        } catch (err) {
          console.error("[CSV] ✗ Load error:", err);
          setError(
            err instanceof Error ? err.message : "Failed to load CSV file"
          );
        } finally {
          setLoading(false);
        }
      };

      if (modalFileUrl) {
        setTitle(modalTitle || "CSV Report");
        // For static files in public folder, use the path directly
        fetchCsv(modalFileUrl);
        return;
      }

      // Fallback to finding report in context
      const report = reports.find((r) => r.id === reportId);
      if (report) {
        setTitle(report.name);
        if (report.file_url) {
          // For static files, use the path directly
          fetchCsv(report.file_url);
        } else {
          // Fallback: try to fetch from reports endpoint
          api.reports
            .get(reportId)
            .then((reportData) => {
              if (reportData.file_url) {
                fetchCsv(getStaticFileUrl(reportData.file_url));
              } else {
                throw new Error("No file URL");
              }
            })
            .catch((err) => {
              console.error("Failed to load CSV:", err);
              setError("Failed to load CSV file");
              setLoading(false);
            });
        }
      } else {
        setLoading(false);
      }
    }
  }, [reportId, reports, modals.csv]);

  const handleClose = () => {
    setModalState({ csv: null });
    setCsvData(null);
    setTitle("");
    setError(null);
  };

  const handleDownload = () => {
    if (csvData) {
      const blob = new Blob([csvData], { type: "text/csv" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${title}.csv`;
      link.click();
      window.URL.revokeObjectURL(url);
    }
  };

  // Parse CSV data with proper handling of quoted fields
  const parseCSV = (csv: string) => {
    const lines = csv.trim().split("\n");
    if (lines.length === 0) return { headers: [], rows: [] };

    // Helper function to parse a CSV line properly
    const parseLine = (line: string): string[] => {
      const result: string[] = [];
      let current = "";
      let inQuotes = false;

      for (let i = 0; i < line.length; i++) {
        const char = line[i];

        if (char === '"') {
          // Toggle quote state
          inQuotes = !inQuotes;
        } else if (char === "," && !inQuotes) {
          // End of field
          result.push(current.trim());
          current = "";
        } else {
          current += char;
        }
      }

      // Push the last field
      result.push(current.trim());
      return result;
    };

    const headers = parseLine(lines[0]);
    const rows = lines
      .slice(1)
      .filter((line) => line.trim().length > 0)
      .map((line) => parseLine(line));

    return { headers, rows };
  };

  const { headers, rows } = csvData
    ? parseCSV(csvData)
    : { headers: [], rows: [] };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="bg-gradient-to-br from-gray-950 to-black border-gray-800/50 max-w-6xl max-h-[85vh]">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle className="text-white flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-green-400" />
              {title || "CSV Viewer"}
            </DialogTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDownload}
              disabled={!csvData}
              className="text-gray-400 hover:text-green-400 hover:bg-green-500/10"
            >
              <Download className="w-4 h-4 mr-2" />
              Download
            </Button>
          </div>
        </DialogHeader>

        <ScrollArea className="h-[70vh] mt-4">
          {loading ? (
            <div className="flex items-center justify-center h-full min-h-[300px]">
              <Loader2 className="w-8 h-8 text-green-400 animate-spin" />
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center h-full text-center p-8 min-h-[300px]">
              <AlertCircle className="w-12 h-12 text-red-400 mb-4" />
              <p className="text-red-400 mb-2">{error}</p>
              <p className="text-gray-500 text-sm">
                Please try again or contact support.
              </p>
            </div>
          ) : csvData && csvData.includes("No table available") ? (
            <div className="flex flex-col items-center justify-center h-full text-center p-8">
              <FileSpreadsheet className="w-16 h-16 text-gray-600 mb-4" />
              <p className="text-lg font-medium text-gray-400 mb-2">
                No table available for this report
              </p>
              <p className="text-sm text-gray-600">
                This report contains summaries only. Please view the PDF version
                for detailed information.
              </p>
            </div>
          ) : headers.length > 0 ? (
            <div className="border border-gray-800 rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-gray-800/50 border-gray-800">
                      {headers.map((header, idx) => (
                        <TableHead
                          key={idx}
                          className="text-gray-300 font-semibold whitespace-nowrap"
                        >
                          {header}
                        </TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {rows.map((row, rowIdx) => (
                      <TableRow
                        key={rowIdx}
                        className="border-gray-800 hover:bg-gray-800/30"
                      >
                        {row.map((cell, cellIdx) => (
                          <TableCell
                            key={cellIdx}
                            className="text-gray-400 text-sm whitespace-nowrap"
                          >
                            {cell || "-"}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500 min-h-[300px]">
              <p>CSV data not available</p>
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
