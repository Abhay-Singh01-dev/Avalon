import React from "react";
import { Brain, Shield, Zap, AlertTriangle, Server, Cloud, FileText } from "lucide-react";

type ThinkingPanelProps = {
  routingMessage: string;
  modeMessage?: string;
  isVisible: boolean;
};

/**
 * ThinkingPanel - Shows routing decisions before streaming starts
 * 
 * Displays PHI detection status and model routing decision in a visually
 * prominent panel that appears before any tokens stream.
 */
export default function ThinkingPanel({ 
  routingMessage, 
  modeMessage,
  isVisible 
}: ThinkingPanelProps) {
  if (!isVisible) return null;

  // Determine if PHI was detected from the message
  const isPHI = routingMessage.toLowerCase().includes("phi detected");
  const isLocal = routingMessage.toLowerCase().includes("local");
  
  // Parse mode from modeMessage
  const getModeInfo = () => {
    if (!modeMessage) return null;
    
    const modeLower = modeMessage.toLowerCase();
    if (modeLower.includes("research")) return { name: "Research Mode", icon: Brain, color: "text-blue-400" };
    if (modeLower.includes("safety")) return { name: "Safety Mode", icon: Shield, color: "text-red-400" };
    if (modeLower.includes("table")) return { name: "Table Mode", icon: Zap, color: "text-purple-400" };
    if (modeLower.includes("document")) return { name: "Document Mode", icon: FileText, color: "text-teal-400" };
    if (modeLower.includes("simple")) return { name: "Simple Mode", icon: Zap, color: "text-green-400" };
    if (modeLower.includes("patient")) return { name: "Patient Mode", icon: Shield, color: "text-yellow-400" };
    return null;
  };

  const modeInfo = getModeInfo();

  return (
    <div className="mb-4 animate-fade-in">
      <div className="bg-gradient-to-r from-gray-900/90 via-gray-800/90 to-gray-900/90 backdrop-blur-md border border-gray-700/50 rounded-xl overflow-hidden shadow-lg">
        {/* Header with animated dots */}
        <div className="px-5 py-3 border-b border-gray-700/50 flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" style={{ animationDelay: "0ms" }} />
            <div className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" style={{ animationDelay: "200ms" }} />
            <div className="w-2 h-2 rounded-full bg-pink-400 animate-pulse" style={{ animationDelay: "400ms" }} />
          </div>
          <span className="text-sm font-semibold text-white tracking-wide uppercase">
            Avalon is Thinking…
          </span>
        </div>

        {/* Content */}
        <div className="px-5 py-4 space-y-3">
          {/* PHI / Routing Decision */}
          <div className="flex items-center gap-3 animate-slide-in">
            {isPHI ? (
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-yellow-500/20 border border-yellow-500/30">
                <Shield className="w-4 h-4 text-yellow-400" />
              </div>
            ) : (
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-green-500/20 border border-green-500/30">
                <Zap className="w-4 h-4 text-green-400" />
              </div>
            )}
            <div className="flex-1">
              <p className={`text-sm font-medium ${isPHI ? "text-yellow-300" : "text-green-300"}`}>
                {routingMessage}
              </p>
            </div>
            {isLocal ? (
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-500/20 border border-blue-500/30">
                <Server className="w-3.5 h-3.5 text-blue-400" />
                <span className="text-xs font-medium text-blue-300">Local</span>
              </div>
            ) : (
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-purple-500/20 border border-purple-500/30">
                <Cloud className="w-3.5 h-3.5 text-purple-400" />
                <span className="text-xs font-medium text-purple-300">Cloud</span>
              </div>
            )}
          </div>

          {/* Mode Information */}
          {modeInfo && (
            <div className="flex items-center gap-3 animate-slide-in" style={{ animationDelay: "100ms" }}>
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gray-700/50 border border-gray-600/50">
                <modeInfo.icon className={`w-4 h-4 ${modeInfo.color}`} />
              </div>
              <p className="text-sm font-medium text-gray-300">
                {modeInfo.name} activated
              </p>
            </div>
          )}
        </div>

        {/* Loading bar */}
        <div className="h-0.5 bg-gray-700/50 overflow-hidden">
          <div className="h-full w-1/3 bg-gradient-to-r from-transparent via-blue-400 to-transparent animate-loading-bar" />
        </div>
      </div>

      {/* CSS Animations */}
      <style>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slide-in {
          from { opacity: 0; transform: translateX(-20px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes loading-bar {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(400%); }
        }
        .animate-fade-in {
          animation: fade-in 0.3s ease-out forwards;
        }
        .animate-slide-in {
          animation: slide-in 0.3s ease-out forwards;
        }
        .animate-loading-bar {
          animation: loading-bar 1.5s linear infinite;
        }
      `}</style>
    </div>
  );
}
