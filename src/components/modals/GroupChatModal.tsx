import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Users, Copy, Check, Loader2, Link2, Share2 } from "lucide-react";
import { api } from "@/lib/api";

interface GroupChatModalProps {
  isOpen: boolean;
  onClose: () => void;
  chatId: string | null;
}

export default function GroupChatModal({
  isOpen,
  onClose,
  chatId,
}: GroupChatModalProps) {
  const [copied, setCopied] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [inviteLink, setInviteLink] = React.useState<string>("");
  const [inviteCode, setInviteCode] = React.useState<string>("");

  // Generate invite link when modal opens with a chatId
  React.useEffect(() => {
    if (isOpen && chatId) {
      generateInviteLink();
    } else if (!isOpen) {
      // Reset state when modal closes
      setInviteLink("");
      setInviteCode("");
      setError(null);
      setCopied(false);
    }
  }, [isOpen, chatId]);

  const generateInviteLink = async () => {
    if (!chatId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.chats.createGroupChat(chatId);
      if (response.status === "success") {
        const baseUrl = window.location.origin;
        const fullLink = `${baseUrl}/invite/${response.invite_code}`;
        setInviteLink(fullLink);
        setInviteCode(response.invite_code);
      } else {
        setError("Failed to generate invite link");
      }
    } catch (err: any) {
      console.error("Error generating group chat link:", err);
      setError(err.message || "Failed to generate invite link");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!inviteLink) return;
    navigator.clipboard.writeText(inviteLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleShareNative = async () => {
    if (!inviteLink) return;
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: "Join my Avalon chat",
          text: "Join this collaborative research discussion on Avalon",
          url: inviteLink,
        });
      } catch (err) {
        // User cancelled or share failed, fall back to copy
        handleCopy();
      }
    } else {
      handleCopy();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-gradient-to-br from-gray-950 to-black border-gray-800/50 max-w-md">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-cyan-400" />
            Start a Group Chat
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          <p className="text-sm text-gray-400">
            Invite collaborators to this conversation using the link below.
            Anyone with this link can join and contribute to the discussion.
          </p>

          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 text-cyan-400 animate-spin mr-2" />
              <span className="text-gray-400">Generating invite link...</span>
            </div>
          ) : error ? (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
              <p className="text-red-400 text-sm">{error}</p>
              <Button
                onClick={generateInviteLink}
                size="sm"
                variant="ghost"
                className="mt-2 text-red-400 hover:text-red-300"
              >
                Try Again
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs text-gray-500 font-medium flex items-center gap-1">
                  <Link2 className="w-3 h-3" />
                  Invite Link
                </label>
                <div className="flex gap-2">
                  <Input
                    value={inviteLink}
                    readOnly
                    className="bg-black border-gray-800 text-gray-300 flex-1 font-mono text-sm"
                    placeholder="Generating..."
                  />
                  <Button
                    onClick={handleCopy}
                    disabled={!inviteLink}
                    className="bg-blue-600 hover:bg-blue-500 flex items-center gap-2 min-w-[100px]"
                  >
                    {copied ? (
                      <>
                        <Check className="w-4 h-4" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4" />
                        Copy
                      </>
                    )}
                  </Button>
                </div>
              </div>

              {/* Native share button for mobile */}
              {typeof navigator !== "undefined" && navigator.share && (
                <Button
                  onClick={handleShareNative}
                  disabled={!inviteLink}
                  variant="outline"
                  className="w-full border-gray-700 hover:bg-gray-800 text-gray-300"
                >
                  <Share2 className="w-4 h-4 mr-2" />
                  Share via...
                </Button>
              )}

              {inviteCode && (
                <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-3">
                  <p className="text-xs text-gray-500 mb-1">Invite Code</p>
                  <p className="text-sm font-mono text-cyan-400">{inviteCode}</p>
                </div>
              )}
            </div>
          )}

          <div className="flex justify-end pt-4 border-t border-gray-800">
            <Button
              onClick={onClose}
              variant="ghost"
              className="text-gray-400 hover:text-gray-200"
            >
              Close
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
