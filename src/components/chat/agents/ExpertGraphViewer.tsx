import React, { useRef, useEffect } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { X } from "lucide-react";

type GraphNode = {
  id: string;
  label?: string;
  type?: string;
  affiliations?: string[];
  expertise?: string[];
  contact?: {
    email?: string | null;
    orcid?: string | null;
    confidence?: number;
    source?: string | null;
  };
  influence_score?: number;
  repurposing_relevance_score?: number;
  size?: number;
  color?: string;
  [key: string]: any;
};

type GraphEdge = {
  source: string | GraphNode;
  target: string | GraphNode;
  type?: string;
  label?: string;
  weight?: number;
  evidence?: string[];
  [key: string]: any;
};

type GraphData = {
  graph_id?: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  meta?: {
    query?: string;
    created_at?: string;
    node_count?: number;
    edge_count?: number;
    channels?: string[];
  };
};

export default function ExpertGraphViewer({ graphData }: { graphData: GraphData }) {
  const graphRef = useRef<any>();
  const [selectedNode, setSelectedNode] = React.useState<GraphNode | null>(null);
  const [hoveredNode, setHoveredNode] = React.useState<GraphNode | null>(null);

  // Prepare graph data
  const nodes = graphData.nodes || [];
  const edges = graphData.edges || [];

  // Color mapping for node types
  const getNodeColor = (node: GraphNode) => {
    if (node.color) return node.color;
    switch (node.type) {
      case "expert":
        return "#3182CE"; // Blue
      case "institution":
        return "#2F855A"; // Green
      case "trial":
        return "#D69E2E"; // Yellow
      case "patent":
        return "#B83280"; // Pink
      default:
        return "#718096"; // Gray
    }
  };

  // Node size based on influence_score or size property
  const getNodeSize = (node: GraphNode) => {
    if (node.size) return node.size;
    if (node.influence_score) {
      return Math.max(5, Math.min(30, node.influence_score / 3));
    }
    return 10;
  };

  // Edge color based on type
  const getEdgeColor = (edge: GraphEdge) => {
    switch (edge.type) {
      case "affiliated_with":
        return "#2F855A"; // Green
      case "co_author":
      case "co_inventor":
        return "#3182CE"; // Blue
      case "investigator_in":
        return "#D69E2E"; // Yellow
      case "inventor_of":
        return "#B83280"; // Pink
      case "collaborated_with":
        return "#805AD5"; // Purple
      default:
        return "#718096"; // Gray
    }
  };

  // Handle node click
  const handleNodeClick = (node: GraphNode) => {
    setSelectedNode(node);
  };

  // Handle background click
  const handleBackgroundClick = () => {
    setSelectedNode(null);
  };

  return (
    <div className="flex h-full bg-black">
      {/* Graph Canvas */}
      <div className="flex-1 relative">
        <ForceGraph2D
          ref={graphRef}
          graphData={{ nodes, links: edges }}
          nodeLabel={(node: GraphNode) => {
            const label = node.label || node.id;
            const type = node.type ? ` (${node.type})` : "";
            return `${label}${type}`;
          }}
          nodeColor={getNodeColor}
          nodeVal={getNodeSize}
          nodeCanvasObject={(node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
            const label = node.label || node.id;
            const size = getNodeSize(node);
            const fontSize = 12 / globalScale;
            ctx.font = `${fontSize}px Sans-Serif`;
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillStyle = "#ffffff";
            ctx.fillText(label, node.x || 0, (node.y || 0) + size + fontSize);
          }}
          linkLabel={(edge: GraphEdge) => {
            return edge.label || edge.type || "connection";
          }}
          linkColor={getEdgeColor}
          linkWidth={(edge: GraphEdge) => {
            return (edge.weight || 0.5) * 2;
          }}
          onNodeClick={handleNodeClick}
          onBackgroundClick={handleBackgroundClick}
          onNodeHover={(node: GraphNode | null) => {
            setHoveredNode(node);
          }}
          cooldownTicks={100}
          onEngineStop={() => {
            if (graphRef.current) {
              graphRef.current.zoomToFit(400, 20);
            }
          }}
        />

        {/* Graph Info Overlay */}
        {graphData.meta && (
          <div className="absolute top-4 left-4 bg-gray-900/80 backdrop-blur-sm border border-gray-800 rounded-lg p-3 text-xs text-gray-300">
            <div className="font-semibold text-white mb-1">Graph Info</div>
            {graphData.meta.query && (
              <div className="mb-1">Query: {graphData.meta.query}</div>
            )}
            <div>Nodes: {nodes.length}</div>
            <div>Edges: {edges.length}</div>
            {graphData.meta.channels && graphData.meta.channels.length > 0 && (
              <div className="mt-1">
                Sources: {graphData.meta.channels.join(", ")}
              </div>
            )}
          </div>
        )}

        {/* Hover Tooltip - Note: Positioning handled by ForceGraph2D's nodeLabel */}
      </div>

      {/* Sidebar with Node Details */}
      {selectedNode && (
        <div className="w-80 bg-gray-900/95 border-l border-gray-800 p-4 overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Node Details</h3>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-gray-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <div className="text-xs text-gray-500 uppercase mb-1">Label</div>
              <div className="text-white font-medium">{selectedNode.label || selectedNode.id}</div>
            </div>

            {selectedNode.type && (
              <div>
                <div className="text-xs text-gray-500 uppercase mb-1">Type</div>
                <div className="text-gray-300 capitalize">{selectedNode.type}</div>
              </div>
            )}

            {selectedNode.affiliations && selectedNode.affiliations.length > 0 && (
              <div>
                <div className="text-xs text-gray-500 uppercase mb-1">Affiliations</div>
                <div className="space-y-1">
                  {selectedNode.affiliations.map((aff, idx) => (
                    <div key={idx} className="text-gray-300">{aff}</div>
                  ))}
                </div>
              </div>
            )}

            {selectedNode.expertise && selectedNode.expertise.length > 0 && (
              <div>
                <div className="text-xs text-gray-500 uppercase mb-1">Expertise</div>
                <div className="flex flex-wrap gap-1">
                  {selectedNode.expertise.map((exp, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded text-xs"
                    >
                      {exp}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {selectedNode.contact && (
              <div>
                <div className="text-xs text-gray-500 uppercase mb-1">Contact</div>
                <div className="space-y-1 text-sm text-gray-300">
                  {selectedNode.contact.email && (
                    <div>Email: {selectedNode.contact.email}</div>
                  )}
                  {selectedNode.contact.orcid && (
                    <div>
                      ORCID:{" "}
                      <a
                        href={`https://orcid.org/${selectedNode.contact.orcid}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300"
                      >
                        {selectedNode.contact.orcid}
                      </a>
                    </div>
                  )}
                  {selectedNode.contact.confidence !== undefined && (
                    <div>Confidence: {selectedNode.contact.confidence}</div>
                  )}
                  {selectedNode.contact.source && (
                    <div>Source: {selectedNode.contact.source}</div>
                  )}
                </div>
              </div>
            )}

            {selectedNode.influence_score !== undefined && (
              <div>
                <div className="text-xs text-gray-500 uppercase mb-1">Influence Score</div>
                <div className="text-white font-semibold">{selectedNode.influence_score}</div>
              </div>
            )}

            {selectedNode.repurposing_relevance_score !== undefined && (
              <div>
                <div className="text-xs text-gray-500 uppercase mb-1">Repurposing Relevance</div>
                <div className="text-white font-semibold">{selectedNode.repurposing_relevance_score}</div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

