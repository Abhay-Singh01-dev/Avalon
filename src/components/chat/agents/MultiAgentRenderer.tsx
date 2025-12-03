import React from "react";
import MarketAgentView from "./MarketAgentView";
import ClinicalTrialsAgentView from "./ClinicalTrialsAgentView";
import PatentsAgentView from "./PatentsAgentView";
import UnmetNeedsAgentView from "./UnmetNeedsAgentView";
import WebEvidenceAgentView from "./WebEvidenceAgentView";
import InternalDocsAgentView from "./InternalDocsAgentView";
import TimelineView from "./TimelineView";
import { Button } from "@/components/ui/button";
import { Network } from "lucide-react";
import { useAppContext } from "@/context/AppContext";

type WorkerData = {
  section: string;
  summary: string;
  details?: any;
  confidence?: number;
  sources?: string[];
  [key: string]: any;
};

type MultiAgentRendererProps = {
  workers?: Record<string, WorkerData>;
  expert_graph_id?: string;
  timeline?: any[];
};

export default function MultiAgentRenderer({
  workers = {},
  expert_graph_id,
  timeline,
}: MultiAgentRendererProps) {
  const { setModalState } = useAppContext();

  const handleViewExpertGraph = () => {
    if (expert_graph_id) {
      setModalState({ graph: { graphId: expert_graph_id } });
    }
  };

  // Render agent-specific views
  const renderAgentView = (agentType: string, worker: WorkerData) => {
    switch (agentType.toLowerCase()) {
      case "market":
        return <MarketAgentView key={agentType} worker={worker} />;
      case "clinical":
      case "clinical_trials":
        return <ClinicalTrialsAgentView key={agentType} worker={worker} />;
      case "patents":
      case "patent":
        return <PatentsAgentView key={agentType} worker={worker} />;
      case "unmet_needs":
      case "unmetneeds":
        return <UnmetNeedsAgentView key={agentType} worker={worker} />;
      case "web_evidence":
      case "web":
        return <WebEvidenceAgentView key={agentType} worker={worker} />;
      case "internal_docs":
      case "internaldocs":
        return <InternalDocsAgentView key={agentType} worker={worker} />;
      default:
        // Generic fallback for unknown agent types
        return (
          <div
            key={agentType}
            className="bg-gray-900/40 border border-gray-800/50 rounded-lg p-4 mt-4"
          >
            <h3 className="text-sm font-semibold text-white mb-2 capitalize">
              {agentType.replace(/_/g, " ")}
            </h3>
            <p className="text-sm text-gray-400 mb-2">{worker.summary}</p>
            {worker.confidence !== undefined && (
              <span className="text-xs text-gray-500">
                Confidence: {worker.confidence}%
              </span>
            )}
          </div>
        );
    }
  };

  return (
    <div className="space-y-0">
      {/* Expert Graph Button */}
      {expert_graph_id && (
        <div className="mt-4 mb-4">
          <Button
            onClick={handleViewExpertGraph}
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white shadow-lg shadow-purple-500/30"
          >
            <Network className="w-4 h-4 mr-2" />
            View Expert Network Graph
          </Button>
        </div>
      )}

      {/* Render all agent views */}
      {Object.entries(workers).map(([agentType, worker]) =>
        renderAgentView(agentType, worker)
      )}

      {/* Timeline */}
      {timeline && timeline.length > 0 && <TimelineView data={{ timeline }} />}
    </div>
  );
}

