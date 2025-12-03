import React, { useState } from "react";
import { CheckCircle2, BarChart3, ExternalLink, Network, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import { mockResearchInsights } from "@/mock/researchInsightsMock";
import ExpertGraphModal from "@/components/modals/ExpertGraphModal";
import AgentTimelineMock from "@/components/chat/AgentTimelineMock";

// Real agent insight format
interface RealResearchInsight {
  section: string;
  key_findings: string[];
  depth: "High" | "Medium" | "Low";
  visualization: string | null;
  links: string[];
  status: "Complete" | "Missing Data" | "Limited";
}

// Mock insight format
interface MockResearchInsight {
  section: string;
  keyFindings: string[];
  depth: string;
  visualization: boolean;
  links: { label: string; url: string }[];
  status: string;
  graphId?: string;
}

// Unified format for rendering
interface UnifiedInsight {
  section: string;
  findings: string[];
  depth: string;
  hasVisualization: boolean;
  links: { label: string; url: string }[];
  status: string;
  graphId?: string;
  isMock: boolean;
}

interface ResearchInsightsTableProps {
  insights?: RealResearchInsight[];
  useMockData?: boolean;
}

// Normalize real agent data to unified format
function normalizeRealInsight(insight: RealResearchInsight): UnifiedInsight {
  return {
    section: insight.section,
    findings: insight.key_findings || [],
    depth: insight.depth,
    hasVisualization: !!insight.visualization,
    links: (insight.links || []).map((url, idx) => ({ label: `Source ${idx + 1}`, url })),
    status: insight.status,
    isMock: false,
  };
}

// Normalize mock data to unified format
function normalizeMockInsight(insight: MockResearchInsight): UnifiedInsight {
  return {
    section: insight.section,
    findings: insight.keyFindings || [],
    depth: insight.depth,
    hasVisualization: insight.visualization,
    links: insight.links || [],
    status: insight.status,
    graphId: insight.graphId,
    isMock: true,
  };
}

export const ResearchInsightsTable: React.FC<ResearchInsightsTableProps> = ({
  insights,
  useMockData = true,
}) => {
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  const [graphModalOpen, setGraphModalOpen] = useState(false);
  const [selectedGraphId, setSelectedGraphId] = useState<string | null>(null);

  // Determine which data to use - real agent data overrides mock
  const hasRealData = insights && insights.length > 0;
  
  // Normalize the data
  const normalizedInsights: UnifiedInsight[] = hasRealData
    ? insights.map(normalizeRealInsight)
    : useMockData
    ? mockResearchInsights.map(normalizeMockInsight)
    : [];

  if (normalizedInsights.length === 0) {
    return null;
  }

  const handleViewGraph = (graphId: string) => {
    setSelectedGraphId(graphId);
    setGraphModalOpen(true);
  };

  const toggleExpand = (idx: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(idx)) {
      newExpanded.delete(idx);
    } else {
      newExpanded.add(idx);
    }
    setExpandedRows(newExpanded);
  };

  const getDepthColor = (depth: string) => {
    switch (depth) {
      case "High":
        return "bg-green-600/20 text-green-400 border-green-500/30";
      case "Medium":
        return "bg-yellow-600/20 text-yellow-400 border-yellow-500/30";
      case "Low":
        return "bg-gray-600/20 text-gray-400 border-gray-500/30";
      default:
        return "bg-gray-600/20 text-gray-400 border-gray-500/30";
    }
  };

  return (
    <>
    {/* Agent Timeline - shows orchestration steps */}
    <AgentTimelineMock className="my-6" />
    
    <div className="research-insights-table my-8 animate-in fade-in duration-500">
      <div className="mb-4 flex items-center gap-3">
        <BarChart3 className="w-6 h-6 text-cyan-400" />
        <h3 className="text-xl font-bold text-gray-100">Research Insights</h3>
        <span className="text-sm text-gray-500 bg-gray-800/50 px-2 py-1 rounded">
          {normalizedInsights.length} {normalizedInsights.length === 1 ? "section" : "sections"}
        </span>
        {!hasRealData && useMockData && (
          <span className="text-xs text-amber-400 bg-amber-500/10 border border-amber-500/30 px-2 py-1 rounded">
            Mock Data
          </span>
        )}
      </div>

      <div className="overflow-x-auto rounded-lg border border-gray-800/50 bg-gray-900/30 backdrop-blur-sm shadow-2xl">
        <table className="w-full border-collapse">
          <thead className="sticky top-0 z-10">
            <tr className="bg-gray-900/90 backdrop-blur-sm border-b border-gray-800">
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider w-[180px]">
                Section
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Key Findings
              </th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-gray-400 uppercase tracking-wider w-[90px]">
                Depth
              </th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-gray-400 uppercase tracking-wider w-[110px]">
                Visualization
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider w-[140px]">
                Links
              </th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-gray-400 uppercase tracking-wider w-[110px]">
                Status
              </th>
            </tr>
          </thead>
          <tbody>
            {normalizedInsights.map((insight, idx) => {
              const isExpanded = expandedRows.has(idx);
              const findings = insight.findings || [];
              const displayFindings = isExpanded
                ? findings
                : findings.slice(0, 3);
              const hasMore = findings.length > 3;
              const isExpertNetwork = insight.section === "Expert Network";

              return (
                <tr
                  key={idx}
                  className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-all duration-200"
                >
                  {/* Section */}
                  <td className="px-4 py-4 text-sm font-semibold text-gray-200 align-top">
                    {insight.section}
                  </td>

                  {/* Key Findings */}
                  <td className="px-4 py-4 text-sm text-gray-300 align-top">
                    {displayFindings.length > 0 ? (
                      <div className="space-y-2">
                        <ul className="space-y-1.5">
                          {displayFindings.map((finding, findingIdx) => (
                            <li
                              key={findingIdx}
                              className="flex items-start gap-2 leading-relaxed"
                            >
                              <span className="text-cyan-400 mt-1.5">•</span>
                              <span>{finding}</span>
                            </li>
                          ))}
                        </ul>
                        {hasMore && (
                          <button
                            onClick={() => toggleExpand(idx)}
                            className="text-xs text-cyan-400 hover:text-cyan-300 font-medium transition-colors"
                          >
                            {isExpanded
                              ? "Show less"
                              : `Show ${findings.length - 3} more...`}
                          </button>
                        )}
                      </div>
                    ) : (
                      <span className="text-gray-600 italic text-xs">
                        No findings available
                      </span>
                    )}
                  </td>

                  {/* Depth Pill */}
                  <td className="px-4 py-4 text-center align-top">
                    <span
                      className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold border ${getDepthColor(
                        insight.depth
                      )}`}
                    >
                      {insight.depth}
                    </span>
                  </td>

                  {/* Visualization */}
                  <td className="px-4 py-4 text-center align-top">
                    {insight.hasVisualization ? (
                      <Button
                        size="sm"
                        variant="ghost"
                        className={`h-7 px-2 text-xs font-medium transition-colors ${
                          isExpertNetwork 
                            ? "text-purple-400 hover:text-purple-300 hover:bg-purple-500/10" 
                            : "text-blue-400 hover:text-blue-300 hover:bg-blue-500/10"
                        }`}
                        onClick={() => {
                          if (isExpertNetwork && insight.graphId) {
                            // Open mind-map graph modal for Expert Network
                            handleViewGraph(insight.graphId);
                          } else {
                            console.log("[ResearchInsights] View visualization for:", insight.section);
                            alert(`${insight.section} visualization will be displayed here.`);
                          }
                        }}
                      >
                        {isExpertNetwork ? (
                          <>
                            <Network className="w-3.5 h-3.5 mr-1" />
                            Mind Map
                          </>
                        ) : (
                          <>
                            <BarChart3 className="w-3.5 h-3.5 mr-1" />
                            View
                          </>
                        )}
                      </Button>
                    ) : (
                      <span className="text-gray-600 text-xs">—</span>
                    )}
                  </td>

                  {/* Links */}
                  <td className="px-4 py-4 text-sm align-top">
                    {insight.links && insight.links.length > 0 ? (
                      <div className="flex flex-col gap-1.5">
                        {insight.links.slice(0, 3).map((link, linkIdx) => (
                          <a
                            key={linkIdx}
                            href={link.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 hover:underline transition-colors"
                          >
                            <ExternalLink className="w-3 h-3" />
                            {link.label}
                          </a>
                        ))}
                        {insight.links.length > 3 && (
                          <span className="text-xs text-gray-600">
                            +{insight.links.length - 3} more
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-gray-600 text-xs">—</span>
                    )}
                  </td>

                  {/* Status */}
                  <td className="px-4 py-4 text-center align-top">
                    {insight.status === "Complete" ? (
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-green-600/20 border border-green-500/30 rounded-md">
                        <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />
                        <span className="text-xs text-green-400 font-medium">
                          Complete
                        </span>
                      </div>
                    ) : insight.status === "Limited" ? (
                      <span className="text-xs text-yellow-400 font-medium">
                        Limited
                      </span>
                    ) : (
                      <span className="text-xs text-gray-600 font-medium">
                        {insight.status}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>

    {/* Expert Graph Modal */}
    <ExpertGraphModal
      isOpen={graphModalOpen}
      onClose={() => {
        setGraphModalOpen(false);
        setSelectedGraphId(null);
      }}
      graphId={selectedGraphId}
    />
    </>
  );
};
