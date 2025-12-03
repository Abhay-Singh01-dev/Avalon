import React, { useState } from "react";
import {
  Brain,
  BarChart3,
  FlaskConical,
  FileText,
  Network,
  Microscope,
  Globe,
  Database,
  CheckCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Scale,
  Ship,
  BookOpen,
} from "lucide-react";
import { cn } from "@/lib/utils";

// Timeline item type
type TimelineStatus = "completed" | "skipped" | "running";

interface TimelineItem {
  agent: string;
  event: string;
  description: string;
  status: TimelineStatus;
  duration: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bgColor: string;
  borderColor: string;
}

// Mock timeline data
const mockTimeline: TimelineItem[] = [
  {
    agent: "Master Agent",
    event: "Task decomposition",
    description: "Analyzing query and distributing to specialized agents",
    status: "completed",
    duration: "0.8s",
    icon: Brain,
    color: "text-purple-400",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/30",
  },
  {
    agent: "Market Intelligence Agent",
    event: "Market landscape analysis",
    description: "Generated market landscape, competitor signals, pricing data",
    status: "completed",
    duration: "1.3s",
    icon: BarChart3,
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/30",
  },
  {
    agent: "Clinical Trials Agent",
    event: "Trial extraction",
    description: "Retrieved active trials, endpoints, enrollment data",
    status: "completed",
    duration: "1.1s",
    icon: FlaskConical,
    color: "text-green-400",
    bgColor: "bg-green-500/10",
    borderColor: "border-green-500/30",
  },
  {
    agent: "Patent Agent",
    event: "Patent extraction",
    description: "Analyzed patent landscape, IP protection, freedom to operate",
    status: "completed",
    duration: "0.9s",
    icon: FileText,
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/30",
  },
  {
    agent: "Safety / PK-PD Agent",
    event: "PK/PD profiling",
    description: "Evaluated pharmacokinetics, toxicity, safety signals",
    status: "completed",
    duration: "1.2s",
    icon: Microscope,
    color: "text-red-400",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/30",
  },
  {
    agent: "Regulatory Agent",
    event: "Regulatory assessment",
    description: "Reviewed FDA pathways, approval timelines, precedents",
    status: "completed",
    duration: "0.7s",
    icon: Scale,
    color: "text-indigo-400",
    bgColor: "bg-indigo-500/10",
    borderColor: "border-indigo-500/30",
  },
  {
    agent: "EXIM Agent",
    event: "Export-import analysis",
    description: "Assessed global trade data, supply chain insights",
    status: "skipped",
    duration: "—",
    icon: Ship,
    color: "text-gray-400",
    bgColor: "bg-gray-500/10",
    borderColor: "border-gray-500/30",
  },
  {
    agent: "Web Intelligence Agent",
    event: "Guideline scanning",
    description: "Scanned treatment guidelines, news, regulatory updates",
    status: "completed",
    duration: "1.5s",
    icon: Globe,
    color: "text-cyan-400",
    bgColor: "bg-cyan-500/10",
    borderColor: "border-cyan-500/30",
  },
  {
    agent: "Internal Docs Agent",
    event: "Document analysis",
    description: "Processed uploaded documents, extracted key insights",
    status: "skipped",
    duration: "—",
    icon: BookOpen,
    color: "text-gray-400",
    bgColor: "bg-gray-500/10",
    borderColor: "border-gray-500/30",
  },
  {
    agent: "Expert Network Agent",
    event: "Network graph built",
    description: "Identified KOLs, research networks, collaboration maps",
    status: "completed",
    duration: "0.6s",
    icon: Network,
    color: "text-pink-400",
    bgColor: "bg-pink-500/10",
    borderColor: "border-pink-500/30",
  },
  {
    agent: "Synthesis Engine",
    event: "Compiling results",
    description: "Aggregating insights, generating structured response",
    status: "completed",
    duration: "2.1s",
    icon: Sparkles,
    color: "text-yellow-400",
    bgColor: "bg-yellow-500/10",
    borderColor: "border-yellow-500/30",
  },
];

interface AgentTimelineMockProps {
  className?: string;
}

export default function AgentTimelineMock({ className }: AgentTimelineMockProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const completedCount = mockTimeline.filter((t) => t.status === "completed").length;
  const totalCount = mockTimeline.length;

  return (
    <div className={cn("w-full max-w-4xl mx-auto", className)}>
      {/* Toggle Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gradient-to-r from-gray-900/80 to-gray-800/80 border border-gray-700/50 rounded-lg hover:border-blue-500/30 transition-all duration-200 group"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500/20 to-cyan-500/20 flex items-center justify-center border border-blue-500/30">
            <Brain className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-left">
            <span className="text-sm font-medium text-gray-200">
              Agent Timeline
            </span>
            <span className="text-xs text-gray-500 ml-2">
              {completedCount}/{totalCount} agents completed
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-green-400 bg-green-500/10 px-2 py-1 rounded border border-green-500/20">
            ✓ Complete
          </span>
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-gray-400 group-hover:text-blue-400 transition-colors" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400 group-hover:text-blue-400 transition-colors" />
          )}
        </div>
      </button>

      {/* Expanded Timeline */}
      {isExpanded && (
        <div className="mt-3 bg-gray-900/50 border border-gray-800 rounded-lg overflow-hidden">
          <div className="p-4 space-y-1">
            {mockTimeline.map((item, index) => {
              const Icon = item.icon;
              const isLast = index === mockTimeline.length - 1;

              return (
                <div key={index} className="relative flex gap-3">
                  {/* Vertical line connector */}
                  {!isLast && (
                    <div className="absolute left-[19px] top-10 w-[2px] h-[calc(100%-8px)] bg-gray-700/50" />
                  )}

                  {/* Icon */}
                  <div
                    className={cn(
                      "w-10 h-10 rounded-lg flex items-center justify-center border z-10 flex-shrink-0",
                      item.status === "completed" && item.bgColor,
                      item.status === "completed" && item.borderColor,
                      item.status === "skipped" && "bg-gray-800/50 border-gray-700",
                      item.status === "running" && "bg-blue-500/20 border-blue-500/50"
                    )}
                  >
                    {item.status === "running" ? (
                      <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
                    ) : (
                      <Icon
                        className={cn(
                          "w-5 h-5",
                          item.status === "completed" ? item.color : "text-gray-500"
                        )}
                      />
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 pb-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span
                          className={cn(
                            "text-sm font-medium",
                            item.status === "completed"
                              ? "text-gray-200"
                              : "text-gray-500"
                          )}
                        >
                          {item.agent}
                        </span>
                        {item.status === "completed" && (
                          <CheckCircle className="w-3.5 h-3.5 text-green-400" />
                        )}
                        {item.status === "skipped" && (
                          <span className="text-xs text-gray-500 bg-gray-800 px-1.5 py-0.5 rounded">
                            Skipped
                          </span>
                        )}
                      </div>
                      <span
                        className={cn(
                          "text-xs",
                          item.status === "completed"
                            ? "text-gray-400"
                            : "text-gray-600"
                        )}
                      >
                        {item.duration}
                      </span>
                    </div>
                    <p
                      className={cn(
                        "text-xs mt-0.5",
                        item.status === "completed"
                          ? "text-gray-400"
                          : "text-gray-600"
                      )}
                    >
                      {item.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Footer */}
          <div className="px-4 py-3 bg-gray-800/30 border-t border-gray-800 flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <Database className="w-3.5 h-3.5" />
              <span>Total execution time: 10.2s</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Powered by</span>
              <span className="text-xs font-medium bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                Avalon Multi-Agent System
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
