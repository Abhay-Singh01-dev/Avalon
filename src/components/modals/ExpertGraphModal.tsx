import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Network, Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAppContext } from "@/context/AppContext";
import { api } from "@/lib/api";
import ExpertGraphViewer from "@/components/chat/agents/ExpertGraphViewer";
import { mockExpertGraph } from "@/mock/mockExpertGraph";

interface ExpertGraphModalProps {
  isOpen?: boolean;
  onClose?: () => void;
  graphId?: string | null;
}

export default function ExpertGraphModal({ 
  isOpen: propsIsOpen, 
  onClose: propsOnClose, 
  graphId: propsGraphId 
}: ExpertGraphModalProps = {}) {
  const { modals, setModalState } = useAppContext();
  const [graphData, setGraphData] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Support both props-based and context-based usage
  const isOpen = propsIsOpen !== undefined ? propsIsOpen : !!modals.graph?.graphId;
  const graphId = propsGraphId !== undefined ? propsGraphId : modals.graph?.graphId;

  React.useEffect(() => {
    if (graphId) {
      // Check for mock graph ID first
      if (graphId === "mock-expert-network") {
        setGraphData(mockExpertGraph);
        setLoading(false);
        setError(null);
        return;
      }

      setLoading(true);
      setError(null);
      api.graph
        .get(graphId)
        .then((data) => {
          // Handle both direct graph response and nested graph structure
          if (data.graph) {
            setGraphData(data.graph);
          } else {
            setGraphData(data);
          }
        })
        .catch((err) => {
          console.error("Failed to load graph:", err);
          setError(err.message || "Failed to load expert network graph");
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [graphId]);

  const handleClose = () => {
    if (propsOnClose) {
      propsOnClose();
    } else {
      setModalState({ graph: null });
    }
    setGraphData(null);
    setError(null);
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="bg-gradient-to-br from-gray-950 to-black border-gray-800/50 max-w-6xl h-[90vh] p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b border-gray-800">
          <div className="flex items-center justify-between">
            <DialogTitle className="text-white flex items-center gap-2">
              <Network className="w-5 h-5 text-purple-400" />
              Expert Network Graph
              {graphId === "mock-expert-network" && (
                <span className="text-xs bg-amber-500/20 text-amber-400 border border-amber-500/30 px-2 py-0.5 rounded ml-2">
                  Mock
                </span>
              )}
            </DialogTitle>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-200 hover:bg-gray-800/50"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <Loader2 className="w-8 h-8 text-purple-400 animate-spin mx-auto mb-4" />
                <p className="text-gray-400">Loading expert network graph...</p>
              </div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <p className="text-red-400 mb-2">Error loading graph</p>
                <p className="text-gray-500 text-sm">{error}</p>
              </div>
            </div>
          ) : graphData ? (
            <ExpertGraphViewer graphData={graphData} />
          ) : (
            <div className="flex items-center justify-center h-full">
              <p className="text-gray-500">No graph data available</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

