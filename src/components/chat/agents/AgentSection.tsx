import React from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ChevronDown, ChevronUp, ExternalLink } from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

type AgentSectionProps = {
  title: string;
  icon: React.ReactNode;
  summary: string;
  confidence?: number;
  sources?: string[];
  children: React.ReactNode;
  defaultOpen?: boolean;
  color?: "blue" | "green" | "purple" | "orange" | "cyan";
};

export default function AgentSection({
  title,
  icon,
  summary,
  confidence,
  sources,
  children,
  defaultOpen = true,
  color = "blue",
}: AgentSectionProps) {
  const [isOpen, setIsOpen] = React.useState(defaultOpen);

  const colorClasses = {
    blue: "bg-blue-500/10 border-blue-500/30 text-blue-400",
    green: "bg-green-500/10 border-green-500/30 text-green-400",
    purple: "bg-purple-500/10 border-purple-500/30 text-purple-400",
    orange: "bg-orange-500/10 border-orange-500/30 text-orange-400",
    cyan: "bg-cyan-500/10 border-cyan-500/30 text-cyan-400",
  };

  const getConfidenceColor = (conf?: number) => {
    if (!conf) return "bg-gray-500/20 text-gray-400";
    if (conf >= 80) return "bg-green-500/20 text-green-400";
    if (conf >= 50) return "bg-yellow-500/20 text-yellow-400";
    return "bg-red-500/20 text-red-400";
  };

  return (
    <Card className="bg-gray-900/40 border-gray-800/50 mt-4">
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger className="w-full">
          <div className="flex items-center justify-between p-4 hover:bg-gray-800/30 transition-colors">
            <div className="flex items-center gap-3 flex-1">
              <div className={`w-10 h-10 rounded-lg ${colorClasses[color]} flex items-center justify-center flex-shrink-0`}>
                {icon}
              </div>
              <div className="flex-1 text-left">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-sm font-semibold text-white">{title}</h3>
                  {confidence !== undefined && (
                    <Badge className={`${getConfidenceColor(confidence)} border text-xs`}>
                      {confidence}% confidence
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-gray-400 line-clamp-1">{summary}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {sources && sources.length > 0 && (
                <Badge variant="outline" className="text-xs text-gray-500 border-gray-700">
                  {sources.length} source{sources.length !== 1 ? "s" : ""}
                </Badge>
              )}
              {isOpen ? (
                <ChevronUp className="w-4 h-4 text-gray-400" />
              ) : (
                <ChevronDown className="w-4 h-4 text-gray-400" />
              )}
            </div>
          </div>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="px-4 pb-4 space-y-4">
            {children}
            {sources && sources.length > 0 && (
              <div className="pt-3 border-t border-gray-800">
                <h4 className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wider">
                  Sources
                </h4>
                <div className="flex flex-wrap gap-2">
                  {sources.map((source, idx) => (
                    <a
                      key={idx}
                      href={source}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
                    >
                      <ExternalLink className="w-3 h-3" />
                      Source {idx + 1}
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}

