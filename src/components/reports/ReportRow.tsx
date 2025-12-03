import React from "react";
import { Button } from "@/components/ui/button";
import {
  FileText,
  Download,
  ExternalLink,
  Trash2,
  FileSpreadsheet,
} from "lucide-react";
import { format } from "date-fns";
import { useAppContext } from "@/context/AppContext";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Report } from "@/lib/api";
import { api } from "@/lib/api";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

interface ReportRowProps {
  report: Report;
  onDelete: (reportId: string) => void;
}

export default function ReportRow({ report, onDelete }: ReportRowProps) {
  const { setModalState } = useAppContext();
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false);
  const [isDeleting, setIsDeleting] = React.useState(false);

  const handleOpenPdf = () => {
    setModalState({ pdf: { reportId: report.id, fileUrl: report.file_url, title: report.name } });
  };

  const handleOpenCsv = () => {
    setModalState({ csv: { reportId: report.id, fileUrl: report.file_url, title: report.name } });
  };

  const handleDownload = async (fileUrl: string | undefined, filename: string) => {
    if (!fileUrl) return;
    
    try {
      // Construct proper URL based on file location
      let url: string;
      if (fileUrl.startsWith("http")) {
        url = fileUrl;
      } else if (fileUrl.startsWith("/uploads/")) {
        // Generated reports from backend
        url = `${BASE_URL}${fileUrl}`;
      } else if (fileUrl.startsWith("/mock_reports/")) {
        // Mock reports from frontend public folder
        url = `${window.location.origin}${fileUrl}`;
      } else {
        url = `${BASE_URL}${fileUrl}`;
      }
      
      // Fetch the file and download
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to download: ${response.status}`);
      }
      
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error("Download failed:", error);
    }
  };

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await api.reports.delete(report.id);
      onDelete(report.id);
      setDeleteDialogOpen(false);
    } catch (error) {
      console.error("Failed to delete report:", error);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <div className="grid grid-cols-12 gap-4 p-4 border-b border-gray-800/50 hover:bg-gray-800/20 transition-all duration-200 group">
        {/* Report Details - Column 1 (3 cols) */}
        <div className="col-span-3 flex items-start gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border border-blue-500/20 flex items-center justify-center flex-shrink-0 group-hover:border-blue-500/40 transition-colors">
            {report.type === "pdf" ? (
              <FileText className="w-5 h-5 text-blue-400" />
            ) : (
              <FileSpreadsheet className="w-5 h-5 text-green-400" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h4 className="text-sm font-semibold text-white truncate">
                {report.name}
              </h4>
              {report.isMock && (
                <span className="text-xs bg-blue-900/40 text-blue-300 px-2 py-0.5 rounded border border-blue-500/30">
                  Mock
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 line-clamp-2">
              {report.about || "No description available"}
            </p>
          </div>
        </div>

        {/* Query - Column 2 (3 cols) */}
        <div className="col-span-3 flex items-center">
          <p className="text-xs text-gray-400 line-clamp-2 leading-relaxed">
            {report.query || "N/A"}
          </p>
        </div>

        {/* Date - Column 3 (2 cols) */}
        <div className="col-span-2 flex items-center">
          <p className="text-xs text-gray-400">
            {report.created_at
              ? format(new Date(report.created_at), "MMM d, yyyy")
              : "N/A"}
          </p>
        </div>

        {/* Actions - Column 4 (4 cols) */}
        <div className="col-span-4 flex items-center justify-end gap-2">
          {/* PDF Button */}
          {report.type === "pdf" && (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleOpenPdf}
                className="h-8 px-3 text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 transition-all"
                title="View PDF"
              >
                <ExternalLink className="w-4 h-4 mr-1" />
                <span className="text-xs">PDF</span>
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() =>
                  handleDownload(report.file_url, `${report.name}.pdf`)
                }
                className="h-8 w-8 text-gray-400 hover:text-gray-300 hover:bg-gray-700/50 transition-all"
                title="Download PDF"
              >
                <Download className="w-4 h-4" />
              </Button>
            </>
          )}

          {/* CSV/XLSX Button */}
          {(report.type === "csv" || report.type === "xlsx") && (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleOpenCsv}
                className="h-8 px-3 text-green-400 hover:text-green-300 hover:bg-green-500/10 transition-all"
                title="View Spreadsheet"
              >
                <ExternalLink className="w-4 h-4 mr-1" />
                <span className="text-xs">{report.type.toUpperCase()}</span>
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() =>
                  handleDownload(
                    report.file_url,
                    `${report.name}.${report.type}`
                  )
                }
                className="h-8 w-8 text-gray-400 hover:text-gray-300 hover:bg-gray-700/50 transition-all"
                title="Download Spreadsheet"
              >
                <Download className="w-4 h-4" />
              </Button>
            </>
          )}

          {/* Delete Button - Hide for mock reports */}
          {!report.isMock && (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setDeleteDialogOpen(true)}
              className="h-8 w-8 text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-all"
              title="Delete Report"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent className="bg-gray-900 border-gray-800 text-gray-200">
          <DialogHeader>
            <DialogTitle className="text-xl font-semibold text-white">
              Delete Report
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <p className="text-gray-400">
              Are you sure you want to delete "{report.name}"? This action
              cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <Button
                variant="ghost"
                onClick={() => setDeleteDialogOpen(false)}
                className="text-gray-400 hover:text-gray-200"
                disabled={isDeleting}
              >
                Cancel
              </Button>
              <Button
                onClick={handleDelete}
                className="bg-red-600 hover:bg-red-500 text-white"
                disabled={isDeleting}
              >
                {isDeleting ? "Deleting..." : "Delete"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
