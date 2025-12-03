import React from "react";
import {
  Brain,
  TrendingUp,
  FlaskConical,
  FileText,
  Globe,
  Shield,
  Database,
  Network,
  FileSearch,
  BarChart3,
  X,
  ChevronDown,
  ChevronUp,
  Lock,
  AlertTriangle,
  FileCheck,
  Zap,
} from "lucide-react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";

type AgentStatus = "pending" | "running" | "completed";

type AgentTimelineState = {
  [agentName: string]: {
    status: AgentStatus;
    message?: string;
  };
};

type AgentTimelineProps = {
  timeline: AgentTimelineState;
  isVisible: boolean;
  onToggle: () => void;
  isCollapsed: boolean;
};

// Agent configuration with colors and icons
const AGENT_CONFIG: Record<string, { icon: React.ComponentType<any>; color: string; name: string }> = {
  master: {
    icon: Brain,
    color: "blue",
    name: "MasterAgent",
  },
  market: {
    icon: TrendingUp,
    color: "green",
    name: "MarketAgent",
  },
  clinical: {
    icon: FlaskConical,
    color: "purple",
    name: "ClinicalTrialsAgent",
  },
  clinical_trials: {
    icon: FlaskConical,
    color: "purple",
    name: "ClinicalTrialsAgent",
  },
  patents: {
    icon: FileText,
    color: "amber",
    name: "PatentAgent",
  },
  patent: {
    icon: FileText,
    color: "amber",
    name: "PatentAgent",
  },
  exim: {
    icon: BarChart3,
    color: "cyan",
    name: "EXIMAgent",
  },
  web: {
    icon: Globe,
    color: "pink",
    name: "WebIntelAgent",
  },
  web_intel: {
    icon: Globe,
    color: "pink",
    name: "WebIntelAgent",
  },
  safety: {
    icon: Shield,
    color: "red",
    name: "SafetyPKPDAgent",
  },
  safety_pkpd: {
    icon: Shield,
    color: "red",
    name: "SafetyPKPDAgent",
  },
  internal_docs: {
    icon: Database,
    color: "teal",
    name: "InternalDocsAgent",
  },
  expert_network: {
    icon: Network,
    color: "orange",
    name: "ExpertNetworkAgent",
  },
  report_generator: {
    icon: FileSearch,
    color: "indigo",
    name: "ReportGeneratorAgent",
  },
  // Security and PHI-related timeline entries
  security: {
    icon: Lock,
    color: "yellow",
    name: "PHI Security",
  },
  phi_detection: {
    icon: AlertTriangle,
    color: "yellow",
    name: "PHI Detection",
  },
  local_routing: {
    icon: Shield,
    color: "green",
    name: "Local Routing",
  },
  // Document processing
  document_processor: {
    icon: FileCheck,
    color: "teal",
    name: "Document Processor",
  },
  // Mode classification
  mode_classifier: {
    icon: Zap,
    color: "purple",
    name: "Mode Classifier",
  },
};

const colorClasses: Record<string, { bg: string; border: string; text: string; pulse: string }> = {
  blue: {
    bg: "bg-blue-500/10",
    border: "border-blue-500/30",
    text: "text-blue-400",
    pulse: "animate-pulse",
  },
  green: {
    bg: "bg-green-500/10",
    border: "border-green-500/30",
    text: "text-green-400",
    pulse: "animate-pulse",
  },
  purple: {
    bg: "bg-purple-500/10",
    border: "border-purple-500/30",
    text: "text-purple-400",
    pulse: "animate-pulse",
  },
  amber: {
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
    text: "text-amber-400",
    pulse: "animate-pulse",
  },
  cyan: {
    bg: "bg-cyan-500/10",
    border: "border-cyan-500/30",
    text: "text-cyan-400",
    pulse: "animate-pulse",
  },
  pink: {
    bg: "bg-pink-500/10",
    border: "border-pink-500/30",
    text: "text-pink-400",
    pulse: "animate-pulse",
  },
  red: {
    bg: "bg-red-500/10",
    border: "border-red-500/30",
    text: "text-red-400",
    pulse: "animate-pulse",
  },
  teal: {
    bg: "bg-teal-500/10",
    border: "border-teal-500/30",
    text: "text-teal-400",
    pulse: "animate-pulse",
  },
  orange: {
    bg: "bg-orange-500/10",
    border: "border-orange-500/30",
    text: "text-orange-400",
    pulse: "animate-pulse",
  },
  indigo: {
    bg: "bg-indigo-500/10",
    border: "border-indigo-500/30",
    text: "text-indigo-400",
    pulse: "animate-pulse",
  },
  yellow: {
    bg: "bg-yellow-500/10",
    border: "border-yellow-500/30",
    text: "text-yellow-400",
    pulse: "animate-pulse",
  },
};

export default function AgentTimeline({ timeline, isVisible, onToggle, isCollapsed }: AgentTimelineProps) {
  if (!isVisible) return null;

  const agents = Object.entries(timeline).sort((a, b) => {
    // Sort by status: running first, then pending, then completed
    const order = { running: 0, pending: 1, completed: 2 };
    return order[a[1].status] - order[b[1].status];
  });

  if (agents.length === 0) return null;

  return (
    <Collapsible open={!isCollapsed} onOpenChange={onToggle}>
      <div className="bg-gray-900/60 backdrop-blur-md border-b border-gray-800/50">
        <CollapsibleTrigger className="w-full px-6 py-3 flex items-center justify-between hover:bg-gray-800/30 transition-colors">
          <div className="flex items-center gap-3">
            <Brain className="w-4 h-4 text-blue-400" />
            <span className="text-sm font-medium text-gray-300">Agent Timeline</span>
            <span className="text-xs text-gray-500">
              {agents.filter(([, state]) => state.status === "running").length} active
            </span>
          </div>
          {isCollapsed ? (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronUp className="w-4 h-4 text-gray-400" />
          )}
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="px-6 pb-4 space-y-2">
            {agents.map(([agentKey, state]) => {
              const config = AGENT_CONFIG[agentKey] || {
                icon: Brain,
                color: "blue",
                name: agentKey,
              };
              const colors = colorClasses[config.color] || colorClasses.blue;
              const Icon = config.icon;
              const isActive = state.status === "running";
              const isCompleted = state.status === "completed";

              return (
                <div
                  key={agentKey}
                  className={`flex items-center gap-3 px-4 py-2.5 rounded-lg border-l-2 transition-all ${
                    isActive
                      ? `${colors.bg} ${colors.border} ${colors.text} ${colors.pulse}`
                      : isCompleted
                      ? "bg-gray-800/30 border-gray-700/30 text-gray-400"
                      : "bg-gray-800/20 border-gray-700/20 text-gray-500"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? colors.text : "text-gray-500"}`} />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium">{config.name}</div>
                    {state.message && (
                      <div className="text-xs text-gray-400 mt-0.5 truncate">{state.message}</div>
                    )}
                  </div>
                  <div className="text-xs text-gray-500">
                    {state.status === "running" && "Running..."}
                    {state.status === "pending" && "Pending"}
                    {state.status === "completed" && "✓"}
                  </div>
                </div>
              );
            })}
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}

