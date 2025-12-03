import React from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Send,
  Mic,
  Bot,
  Paperclip,
  X,
  FileText,
  Plus,
  Loader2,
  MicOff,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { useAppContext } from "@/context/AppContext";
import { api } from "@/lib/api";
import { useVoiceRecorder } from "./VoiceRecorder";
import WaveformVisualizer from "./WaveformVisualizer";
import VoiceChatModal from "@/components/modals/VoiceChatModal";

export default function ChatInput({
  onSend,
  isLoading,
  onCancel,
  isStreaming,
}) {
  const { uploads, addUpload, removeUpload } = useAppContext();
  const [message, setMessage] = React.useState("");
  const [uploadingFiles, setUploadingFiles] = React.useState<Set<string>>(
    new Set()
  );
  const [voiceChatOpen, setVoiceChatOpen] = React.useState(false);
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  // Premium voice recorder with waveform, auto-stop, and echo suppression
  const voice = useVoiceRecorder({
    onFinal: (text) => {
      // Replace input with final transcript (prevents repetition)
      console.log("[ChatInput] Final voice text:", text);
      setMessage(text);
    },
    onInterim: (text) => {
      // Show live transcription (will be cleared when final text arrives)
      console.log("[ChatInput] Interim voice text:", text);
    },
    onStart: () => {
      console.log("[ChatInput] Voice recording started");
    },
    onStop: () => {
      console.log("[ChatInput] Voice recording stopped");
    },
    onError: (error) => {
      console.error("[ChatInput] Voice error:", error);
    },
    autoStopOnSilence: true,
    silenceThreshold: 0.01,
    silenceDuration: 2000,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSend(message);
      setMessage("");
      // Clear uploads after sending (they're attached to the message)
      uploads.forEach((file) => removeUpload(file.id));
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleTextareaChange = (e) => {
    setMessage(e.target.value);
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, 200) + "px";
    }
  };

  const toggleVoiceRecording = React.useCallback(() => {
    console.log(
      "[ChatInput] Toggle voice recording, current state:",
      voice.isListening
    );

    if (voice.isListening) {
      console.log("[ChatInput] Calling voice.stop()");
      voice.stop();
    } else {
      console.log("[ChatInput] Calling voice.start()");
      voice.start();
    }
  }, [voice.isListening, voice.stop, voice.start]);
  const handleChatWithAgent = () => {
    console.log("[ChatInput] Chat with Agent clicked - opening voice chat modal");
    setVoiceChatOpen(true);
  };

  const handleFileUpload = async (files: FileList | File[]) => {
    const fileArray = Array.from(files);
    for (const file of fileArray) {
      const tempId = `temp-${Date.now()}-${Math.random()}`;
      setUploadingFiles((prev) => new Set(prev).add(tempId));

      try {
        const result = await api.uploads.uploadFile(file);
        addUpload({
          id: result.file_id,
          name: result.name,
          size: file.size,
        });
      } catch (error) {
        console.error("File upload failed:", error);
      } finally {
        setUploadingFiles((prev) => {
          const next = new Set(prev);
          next.delete(tempId);
          return next;
        });
      }
    }
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFileUpload(e.target.files);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.files) {
      handleFileUpload(e.dataTransfer.files);
    }
  };

  const removeFile = (id: string) => {
    removeUpload(id);
  };

  const openFilePicker = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="border-t border-gray-800/30 bg-gradient-to-t from-gray-950/90 via-black/80 to-gray-950/90 backdrop-blur-sm p-6">
      <div className="max-w-4xl mx-auto">
        {/* Listening Banner with Waveform */}
        {voice.isListening && (
          <div className="mb-4 p-4 bg-gradient-to-r from-blue-500/20 to-cyan-500/20 border border-blue-500/40 rounded-xl backdrop-blur-sm animate-pulse">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <Mic className="w-5 h-5 text-blue-400 animate-pulse" />
                  <div className="absolute inset-0 animate-ping">
                    <Mic className="w-5 h-5 text-blue-400 opacity-75" />
                  </div>
                </div>
                <span className="text-blue-300 font-medium">Listening...</span>
              </div>
              <button
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  toggleVoiceRecording();
                }}
                className="text-red-400 hover:text-red-300 transition-colors"
              >
                <MicOff className="w-4 h-4" />
              </button>
            </div>

            {/* Waveform Visualizer */}
            <div className="flex items-center justify-center mt-2">
              <WaveformVisualizer
                volumeLevel={voice.volumeLevel}
                isActive={voice.isListening}
                width={300}
                height={40}
                barCount={25}
                barColor="#60a5fa"
                barGap={3}
              />
            </div>

            {/* Interim Transcript */}
            {voice.interimTranscript && (
              <div className="mt-3 p-2 bg-blue-900/30 rounded-lg text-blue-200 text-sm italic">
                "{voice.interimTranscript}"
              </div>
            )}
          </div>
        )}

        {/* Error Message */}
        {voice.error && (
          <div className="mb-3 p-3 bg-red-500/20 border border-red-500/40 rounded-lg text-red-300 text-sm">
            {voice.error}
          </div>
        )}

        <form
          onSubmit={handleSubmit}
          className="relative"
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.txt,.csv,.xlsx,.xls,.png,.jpg,.jpeg"
            onChange={handleFileSelect}
            className="hidden"
          />

          {/* Uploaded Files Bar */}
          {(uploads.length > 0 || uploadingFiles.size > 0) && (
            <div className="mb-3 flex items-center gap-2 flex-wrap">
              {uploads.map((file) => (
                <Badge
                  key={file.id}
                  className="bg-green-500/20 text-green-400 border-green-500/30 px-3 py-1 flex items-center gap-2"
                >
                  <FileText className="w-3 h-3" />
                  {file.name}
                  {file.size && ` (${(file.size / 1024).toFixed(2)} KB)`}
                  <button
                    type="button"
                    onClick={() => removeFile(file.id)}
                    className="ml-1 hover:text-red-400"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              ))}
              {uploadingFiles.size > 0 && (
                <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30 px-3 py-1">
                  <Loader2 className="w-3 h-3 mr-1 animate-spin inline" />
                  Uploading...
                </Badge>
              )}
            </div>
          )}

          <div
            className={`relative bg-gray-900/40 border rounded-2xl p-4 transition-all ${
              voice.isListening
                ? "border-blue-500/60 shadow-lg shadow-blue-500/20 ring-2 ring-blue-500/30"
                : "border-gray-800/50 focus-within:border-blue-500/60 focus-within:shadow-lg focus-within:shadow-blue-500/20"
            }`}
          >
            <div className="relative">
              <Textarea
                ref={textareaRef}
                value={message}
                onChange={handleTextareaChange}
                onKeyDown={handleKeyDown}
                placeholder={
                  voice.isListening
                    ? "Listening to your voice..."
                    : "Ask about pharma research, clinical trials, patents, market analysis... (Pharma-only AI)"
                }
                className="w-full pr-28 bg-transparent border-0 text-gray-200 placeholder:text-gray-600 resize-none focus-visible:ring-0 focus-visible:ring-offset-0 min-h-[60px] max-h-[200px]"
                disabled={isLoading}
              />

              {/* Buttons Inside Text Box */}
              <div className="absolute right-2 bottom-2 flex items-center gap-1">
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  onClick={openFilePicker}
                  className="h-8 w-8 text-gray-400 hover:text-green-400 hover:bg-green-500/10 transition-all"
                  disabled={isLoading || uploadingFiles.size > 0}
                  title="Upload file"
                >
                  <Plus className="w-4 h-4" />
                </Button>

                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  onClick={handleChatWithAgent}
                  className="h-8 w-8 text-gray-400 hover:text-cyan-400 hover:bg-cyan-500/10 transition-all"
                  disabled={isLoading}
                  title="Chat with Agent"
                >
                  <Bot className="w-4 h-4" />
                </Button>

                {/* Premium Mic Button with Animation */}
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    toggleVoiceRecording();
                  }}
                  className={`h-8 w-8 transition-all duration-300 ${
                    voice.isListening
                      ? "text-red-400 bg-red-500/30 shadow-lg shadow-red-500/50 ring-2 ring-red-400/50 animate-pulse scale-110"
                      : voice.isSupported
                      ? "text-gray-400 hover:text-blue-400 hover:bg-blue-500/20 hover:shadow-lg hover:shadow-blue-500/30 hover:scale-105"
                      : "text-gray-600 opacity-50 cursor-not-allowed"
                  }`}
                  disabled={isLoading || !voice.isSupported}
                  title={
                    !voice.isSupported
                      ? "Voice input not supported in this browser"
                      : voice.isListening
                      ? "Stop recording (or wait for auto-stop)"
                      : "Start voice input with ChatGPT-style interface"
                  }
                >
                  {voice.isListening ? (
                    <MicOff className="w-4 h-4" />
                  ) : (
                    <Mic className="w-4 h-4" />
                  )}
                </Button>

                {isStreaming ? (
                  <Button
                    type="button"
                    size="icon"
                    onClick={onCancel}
                    className="h-8 w-8 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white shadow-lg shadow-red-500/30 transition-all hover:shadow-red-500/50 hover:scale-105"
                    title="Cancel streaming"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                ) : (
                  <Button
                    type="submit"
                    size="icon"
                    disabled={!message.trim() || isLoading}
                    className="h-8 w-8 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white shadow-lg shadow-blue-500/30 transition-all hover:shadow-blue-500/50 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
                    title="Send message"
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                )}
              </div>
            </div>
          </div>
        </form>

        <p className="text-xs text-center text-gray-600 mt-3">
          Avalon can make mistakes. Verify critical information.
        </p>
      </div>

      {/* Voice Chat Modal */}
      <VoiceChatModal
        isOpen={voiceChatOpen}
        onClose={() => setVoiceChatOpen(false)}
      />
    </div>
  );
}
