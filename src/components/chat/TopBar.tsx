import React from "react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Share2,
  Copy,
  Twitter,
  MessageCircle,
  FileText,
  Bell,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAppContext } from "@/context/AppContext";
import { api } from "@/lib/api";
import { useNavigate } from "react-router-dom";

export default function TopBar({ chatTitle = "Avalon" }) {
  const { currentConversation, refreshAll } = useAppContext();
  const navigate = useNavigate();
  const [shareOpen, setShareOpen] = React.useState(false);
  const [shareUrl, setShareUrl] = React.useState("");
  const [generateReportOpen, setGenerateReportOpen] = React.useState(false);
  const [reportTitle, setReportTitle] = React.useState("");
  const [reportDescription, setReportDescription] = React.useState("");
  const [generatingReport, setGeneratingReport] = React.useState(false);
  const [notifications, setNotifications] = React.useState([
    { id: 1, message: "New clinical trial data available for Oncology", time: "2 hours ago", read: false },
    { id: 2, message: "Patent expiry alert: Drug XYZ-001", time: "1 day ago", read: false },
    { id: 3, message: "Market report updated for Cardiology sector", time: "2 days ago", read: true },
  ]);

  React.useEffect(() => {
    if (currentConversation?.id) {
      const url = `${window.location.origin}/chat?conversation=${currentConversation.id}`;
      setShareUrl(url);
    }
  }, [currentConversation]);

  const handleShare = (platform: string) => {
    const text = encodeURIComponent(`Check out this research: ${chatTitle}`);
    const url = encodeURIComponent(shareUrl);

    const urls: Record<string, string> = {
      twitter: `https://twitter.com/intent/tweet?text=${text}&url=${url}`,
      whatsapp: `https://wa.me/?text=${text}%20${url}`,
    };

    if (urls[platform]) {
      window.open(urls[platform], "_blank");
    }
  };

  const copyLink = () => {
    navigator.clipboard.writeText(shareUrl);
  };

  const handleGenerateReport = async () => {
    if (!currentConversation?.id) return;
    setGeneratingReport(true);
    try {
      // Extract worker data from the last assistant message
      const lastMessage = currentConversation.messages
        ?.filter((msg) => msg.role === "assistant")
        .pop();
      const workers = lastMessage?.metadata?.workers || {};

      const response = await api.reports.generate({
        report_type: "comprehensive",
        title: reportTitle || `Report: ${chatTitle}`,
        description: reportDescription || `Generated from conversation: ${chatTitle}`,
        format: "pdf",
        conversation_id: currentConversation.id,
        parameters: {
          workers,
          query: currentConversation.messages?.[0]?.content || "",
        },
      });

      // Refresh reports list
      await refreshAll();

      // Close dialog and navigate to reports
      setGenerateReportOpen(false);
      setReportTitle("");
      setReportDescription("");
      navigate("/reports");
    } catch (error) {
      console.error("Failed to generate report:", error);
    } finally {
      setGeneratingReport(false);
    }
  };

  return (
    <>
      <div className="h-16 border-b border-gray-800/30 flex items-center justify-between px-6 bg-gradient-to-r from-gray-950/80 via-black/50 to-gray-950/80 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-medium text-gray-300">{chatTitle}</h2>
        </div>

            <div className="flex items-center gap-2">
              {/* Notification Button */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-gray-400 hover:text-yellow-400 hover:bg-yellow-500/10 transition-all relative"
                  >
                    <Bell className="w-4 h-4" />
                    {notifications.filter(n => !n.read).length > 0 && (
                      <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-[10px] flex items-center justify-center text-white font-bold">
                        {notifications.filter(n => !n.read).length}
                      </span>
                    )}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  align="end"
                  className="bg-gray-900 border-gray-800 text-gray-200 w-72 max-w-[calc(100vw-2rem)] z-50 mt-2 mr-2"
                >
                  <div className="px-3 py-2 border-b border-gray-800">
                    <h4 className="font-semibold text-white">Notifications</h4>
                  </div>
                  {notifications.length === 0 ? (
                    <div className="px-3 py-4 text-center text-gray-500 text-sm">
                      No notifications
                    </div>
                  ) : (
                    notifications.map((notif) => (
                      <DropdownMenuItem
                        key={notif.id}
                        className={`hover:bg-gray-800 cursor-pointer flex flex-col items-start gap-1 p-3 ${
                          !notif.read ? 'bg-blue-500/5' : ''
                        }`}
                        onClick={() => {
                          setNotifications(prev =>
                            prev.map(n => n.id === notif.id ? { ...n, read: true } : n)
                          );
                        }}
                      >
                        <span className="text-sm text-gray-200">{notif.message}</span>
                        <span className="text-xs text-gray-500">{notif.time}</span>
                        {!notif.read && (
                          <span className="absolute right-3 top-1/2 -translate-y-1/2 w-2 h-2 bg-blue-500 rounded-full"></span>
                        )}
                      </DropdownMenuItem>
                    ))
                  )}
                  <DropdownMenuSeparator className="bg-gray-800" />
                  <DropdownMenuItem
                    className="hover:bg-gray-800 cursor-pointer justify-center text-blue-400 text-sm"
                    onClick={() => {
                      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
                    }}
                  >
                    Mark all as read
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              {/* Generate Report Button */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setReportTitle(`Report: ${chatTitle}`);
                  setGenerateReportOpen(true);
                }}
                className="text-gray-400 hover:text-green-400 hover:bg-green-500/10 transition-all"
                disabled={!currentConversation?.id}
              >
                <FileText className="w-4 h-4 mr-2" />
                Generate Report
              </Button>

              {/* Share Button */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShareOpen(true)}
                className="text-gray-400 hover:text-cyan-400 hover:bg-cyan-500/10 transition-all"
              >
                <Share2 className="w-4 h-4 mr-2" />
                Share
              </Button>
        </div>
      </div>

      {/* Share Dialog */}
      <Dialog open={shareOpen} onOpenChange={setShareOpen}>
        <DialogContent className="bg-gray-900 border-gray-800 text-gray-200">
          <DialogHeader>
            <DialogTitle className="text-xl font-semibold text-white">
              Share Research
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="flex items-center gap-2">
              <Input
                value={shareUrl}
                readOnly
                className="flex-1 bg-black border-gray-800 text-gray-300"
              />
              <Button
                onClick={copyLink}
                className="bg-blue-600 hover:bg-blue-500"
              >
                <Copy className="w-4 h-4" />
              </Button>
            </div>

            <div className="flex gap-2">
              <Button
                onClick={() => handleShare("twitter")}
                className="flex-1 bg-sky-500 hover:bg-sky-600"
              >
                <Twitter className="w-4 h-4 mr-2" />
                Twitter
              </Button>
              <Button
                onClick={() => handleShare("whatsapp")}
                className="flex-1 bg-green-500 hover:bg-green-600"
              >
                <MessageCircle className="w-4 h-4 mr-2" />
                WhatsApp
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

        {/* Generate Report Dialog */}
        <Dialog open={generateReportOpen} onOpenChange={setGenerateReportOpen}>
          <DialogContent className="bg-gradient-to-br from-gray-950 to-black border-gray-800/50 text-gray-200">
            <DialogHeader>
              <DialogTitle className="text-xl font-semibold text-white">
                Generate Report
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label htmlFor="report-title" className="text-gray-300">
                  Report Title
                </Label>
                <Input
                  id="report-title"
                  value={reportTitle}
                  onChange={(e) => setReportTitle(e.target.value)}
                  placeholder="Enter report title"
                  className="bg-black border-gray-800 text-gray-300"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="report-description" className="text-gray-300">
                  Description (Optional)
                </Label>
                <Input
                  id="report-description"
                  value={reportDescription}
                  onChange={(e) => setReportDescription(e.target.value)}
                  placeholder="Enter report description"
                  className="bg-black border-gray-800 text-gray-300"
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button
                  variant="ghost"
                  onClick={() => {
                    setGenerateReportOpen(false);
                    setReportTitle("");
                    setReportDescription("");
                  }}
                  className="text-gray-400 hover:text-gray-200"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleGenerateReport}
                  disabled={generatingReport || !reportTitle.trim()}
                  className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 shadow-lg shadow-green-500/30 hover:shadow-green-500/50 hover:scale-[1.02] transition-all"
                >
                  {generatingReport ? "Generating..." : "Generate Report"}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </>
    );
  }
