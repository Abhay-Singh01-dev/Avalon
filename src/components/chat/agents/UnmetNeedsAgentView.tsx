import React from "react";
import { AlertCircle, Target, TrendingDown } from "lucide-react";
import AgentSection from "./AgentSection";

type UnmetNeedsAgentData = {
  section: string;
  summary: string;
  details?: {
    unmet_needs?: Array<{
      need?: string;
      description?: string;
      priority?: string;
      impact_score?: number;
      affected_population?: string;
    }>;
    gaps?: string[];
    opportunities?: string[];
    [key: string]: any;
  };
  confidence?: number;
  sources?: string[];
};

export default function UnmetNeedsAgentView({ worker }: { worker: UnmetNeedsAgentData }) {
  const details = worker.details || {};
  const unmetNeeds = details.unmet_needs || [];
  const gaps = details.gaps || [];
  const opportunities = details.opportunities || [];

  const getPriorityColor = (priority?: string) => {
    if (!priority) return "bg-gray-500/20 text-gray-400";
    const p = priority.toLowerCase();
    if (p.includes("high") || p.includes("critical")) return "bg-red-500/20 text-red-400";
    if (p.includes("medium")) return "bg-yellow-500/20 text-yellow-400";
    return "bg-blue-500/20 text-blue-400";
  };

  return (
    <AgentSection
      title="Unmet Needs"
      icon={<AlertCircle className="w-5 h-5" />}
      summary={worker.summary}
      confidence={worker.confidence}
      sources={worker.sources}
      color="orange"
    >
      <div className="space-y-4">
        {/* Unmet Needs List */}
        {unmetNeeds.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
              Identified Unmet Needs
            </h4>
            <div className="space-y-3">
              {unmetNeeds.map((need, idx) => (
                <div
                  key={idx}
                  className="bg-gray-800/30 rounded-lg p-3 border border-gray-800"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Target className="w-4 h-4 text-orange-400" />
                      <h5 className="text-sm font-semibold text-white">
                        {need.need || `Unmet Need ${idx + 1}`}
                      </h5>
                    </div>
                    {need.priority && (
                      <span
                        className={`px-2 py-1 rounded text-xs ${getPriorityColor(need.priority)}`}
                      >
                        {need.priority}
                      </span>
                    )}
                  </div>
                  {need.description && (
                    <p className="text-xs text-gray-400 mb-2">{need.description}</p>
                  )}
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    {need.impact_score !== undefined && (
                      <div className="flex items-center gap-1">
                        <TrendingDown className="w-3 h-3" />
                        <span>Impact: {need.impact_score}</span>
                      </div>
                    )}
                    {need.affected_population && (
                      <span>Population: {need.affected_population}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Gaps */}
        {gaps.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
              Research Gaps
            </h4>
            <ul className="space-y-1">
              {gaps.map((gap, idx) => (
                <li key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                  <span className="text-orange-400 mt-1">•</span>
                  <span>{gap}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Opportunities */}
        {opportunities.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
              Opportunities
            </h4>
            <ul className="space-y-1">
              {opportunities.map((opportunity, idx) => (
                <li key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                  <span className="text-green-400 mt-1">•</span>
                  <span>{opportunity}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </AgentSection>
  );
}

