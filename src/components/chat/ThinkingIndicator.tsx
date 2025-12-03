import React from "react";
import { Sparkles } from "lucide-react";

function ThinkingIndicator() {
  return (
    <>
      <div
        className="flex gap-4 mb-6 justify-start"
        style={{ minHeight: "60px" }}
      >
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 via-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/30 flex-shrink-0">
          <Sparkles className="w-5 h-5 text-white" />
        </div>

        <div className="max-w-3xl rounded-2xl px-5 py-4 bg-gray-900/50 border border-gray-800">
          <div className="flex items-center gap-2">
            <span className="text-gray-400 italic opacity-70 text-sm">
              Thinking
            </span>
            <div className="flex gap-1.5 items-center">
              <span className="thinking-dot thinking-dot-1" />
              <span className="thinking-dot thinking-dot-2" />
              <span className="thinking-dot thinking-dot-3" />
            </div>
          </div>
        </div>
      </div>

      <style>{`
        .thinking-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background-color: rgb(156, 163, 175);
          opacity: 0.7;
          animation: thinking-pulse 1.4s ease-in-out infinite;
        }
        
        .thinking-dot-1 {
          animation-delay: 0ms;
        }
        
        .thinking-dot-2 {
          animation-delay: 200ms;
        }
        
        .thinking-dot-3 {
          animation-delay: 400ms;
        }
        
        @keyframes thinking-pulse {
          0%, 100% {
            opacity: 0.3;
            transform: scale(0.8);
          }
          50% {
            opacity: 0.9;
            transform: scale(1);
          }
        }
      `}</style>
    </>
  );
}

export default React.memo(ThinkingIndicator);
