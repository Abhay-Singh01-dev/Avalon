import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { FileText, Download, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAppContext } from "@/context/AppContext";
import { api } from "@/lib/api";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export default function PdfViewerModal() {
  const { modals, setModalState, reports } = useAppContext();
  const [loading, setLoading] = React.useState(false);
  const [pdfUrl, setPdfUrl] = React.useState<string | null>(null);
  const [title, setTitle] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);

  const isOpen = !!modals.pdf?.reportId;
  const reportId = modals.pdf?.reportId;

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

  React.useEffect(() => {
    let currentObjectUrl: string | null = null;

    if (reportId) {
      setError(null);
      setLoading(true);

      // First check if fileUrl and title are provided in modal state (for mock reports)
      const modalFileUrl = modals.pdf?.fileUrl;
      const modalTitle = modals.pdf?.title;

      const loadPdfAsBlob = async (fileUrl: string) => {
        try {
          // Construct proper URL based on file location
          const fullUrl = fileUrl.startsWith("/uploads/")
            ? `${BASE_URL}${fileUrl}` // Backend generated reports
            : fileUrl.startsWith("http")
            ? fileUrl // Already absolute
            : `${window.location.origin}${fileUrl}`; // Mock reports in public/

          console.log("[PDF] Fetching:", fullUrl);
          // Force fresh fetch - bypass cache completely
          const response = await fetch(fullUrl, { 
            cache: 'no-store',
            headers: {
              'Cache-Control': 'no-cache, no-store, must-revalidate',
              'Pragma': 'no-cache',
              'Expires': '0'
            }
          });
          console.log("[PDF] Response status:", response.status);
          const contentType = response.headers.get("content-type") || "";
          console.log("[PDF] Content-Type:", contentType);

          if (!response.ok) {
            throw new Error(`Failed to fetch PDF: ${response.status}`);
          }

          const blob = await response.blob();
          console.log("[PDF] Blob type:", blob.type);
          console.log("[PDF] Blob size:", blob.size);

          // Validate that we got some content
          if (blob.size === 0) {
            throw new Error("PDF file is empty");
          }

          // Create proper PDF blob with correct MIME type
          const pdfBlob = new Blob([blob], { type: "application/pdf" });
          const objectUrl = URL.createObjectURL(pdfBlob);
          currentObjectUrl = objectUrl;

          console.log("[PDF] Created blob URL:", objectUrl);
          console.log("[PDF] ✓ PDF loaded successfully");
          setPdfUrl(objectUrl);
          setLoading(false);
        } catch (err) {
          console.error("[PDF] ✗ Load error:", err);
          setError(
            err instanceof Error ? err.message : "Failed to load PDF report"
          );
          setLoading(false);
        }
      };

      if (modalFileUrl) {
        setTitle(modalTitle || "PDF Report");
        loadPdfAsBlob(modalFileUrl);
        return;
      }

      // Fallback to finding report in context
      const report = reports.find((r) => r.id === reportId);
      if (report) {
        setTitle(report.name);
        if (report.file_url) {
          loadPdfAsBlob(report.file_url);
        } else {
          // Fallback: try to fetch from reports endpoint
          api.reports
            .get(reportId)
            .then((reportData) => {
              if (reportData.file_url) {
                loadPdfAsBlob(getStaticFileUrl(reportData.file_url));
              } else {
                throw new Error("No file URL available");
              }
            })
            .catch((err) => {
              console.error("Failed to load PDF:", err);
              setError("Failed to load PDF report");
              setLoading(false);
            });
        }
      } else {
        setLoading(false);
      }
    }

    // Cleanup function to revoke object URL on unmount or when reportId changes
    return () => {
      if (currentObjectUrl) {
        URL.revokeObjectURL(currentObjectUrl);
      }
    };
  }, [reportId, reports, modals.pdf]);

  const handleClose = () => {
    // Revoke object URL to free memory
    if (pdfUrl && pdfUrl.startsWith("blob:")) {
      URL.revokeObjectURL(pdfUrl);
    }
    setModalState({ pdf: null });
    setPdfUrl(null);
    setTitle("");
    setError(null);
  };

  const handleDownload = () => {
    if (pdfUrl) {
      const link = document.createElement("a");
      link.href = pdfUrl;
      link.download = `${title}.pdf`;
      link.click();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="bg-gradient-to-br from-gray-950 to-black border-gray-800/50 max-w-5xl h-[85vh]">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle className="text-white flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-400" />
              {title || "PDF Viewer"}
            </DialogTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDownload}
              disabled={!pdfUrl}
              className="text-gray-400 hover:text-blue-400 hover:bg-blue-500/10"
            >
              <Download className="w-4 h-4 mr-2" />
              Download
            </Button>
          </div>
        </DialogHeader>

        <div className="flex-1 bg-black rounded-lg border border-gray-800 overflow-hidden mt-4">
          {loading ? (
            <div
              className="flex items-center justify-center h-full"
              style={{ minHeight: "70vh" }}
            >
              <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
            </div>
          ) : error ? (
            <div
              className="flex flex-col items-center justify-center h-full text-center p-8"
              style={{ minHeight: "70vh" }}
            >
              <AlertCircle className="w-12 h-12 text-red-400 mb-4" />
              <p className="text-red-400 mb-2">{error}</p>
              <p className="text-gray-500 text-sm">
                Please try again or contact support.
              </p>
            </div>
          ) : pdfUrl ? (
            <object
              data={pdfUrl}
              type="application/pdf"
              className="w-full h-full"
              style={{ minHeight: "70vh" }}
            >
              <iframe
                src={pdfUrl}
                className="w-full h-full"
                style={{ minHeight: "70vh" }}
                title={title}
              >
                <p className="text-gray-400 p-4">
                  Unable to display PDF.{" "}
                  <a
                    href={pdfUrl}
                    download
                    className="text-blue-400 hover:underline"
                  >
                    Download instead
                  </a>
                </p>
              </iframe>
            </object>
          ) : (
            <div
              className="flex items-center justify-center h-full text-gray-500"
              style={{ minHeight: "70vh" }}
            >
              <p>PDF not available</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
