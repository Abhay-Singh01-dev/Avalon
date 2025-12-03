import React from "react";
import { FileText, Calendar, Building2 } from "lucide-react";
import AgentSection from "./AgentSection";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

type PatentsAgentData = {
  section: string;
  summary: string;
  details?: {
    patent_landscape?: Array<{
      patent_number?: string;
      title?: string;
      assignee?: string;
      filing_date?: string;
      grant_date?: string;
      status?: string;
      claims?: string[];
      relevance_score?: number;
    }>;
    patent_summary?: {
      total_patents?: number;
      granted?: number;
      pending?: number;
      key_assignees?: string[];
    };
    [key: string]: any;
  };
  confidence?: number;
  sources?: string[];
};

export default function PatentsAgentView({ worker }: { worker: PatentsAgentData }) {
  const details = worker.details || {};
  const patents = details.patent_landscape || [];
  const patentSummary = details.patent_summary || {};

  const getStatusColor = (status?: string) => {
    if (!status) return "bg-gray-500/20 text-gray-400";
    const s = status.toLowerCase();
    if (s.includes("granted")) return "bg-green-500/20 text-green-400";
    if (s.includes("pending") || s.includes("application")) return "bg-yellow-500/20 text-yellow-400";
    if (s.includes("expired")) return "bg-red-500/20 text-red-400";
    return "bg-gray-500/20 text-gray-400";
  };

  return (
    <AgentSection
      title="Patent Landscape"
      icon={<FileText className="w-5 h-5" />}
      summary={worker.summary}
      confidence={worker.confidence}
      sources={worker.sources}
      color="purple"
    >
      <div className="space-y-4">
        {/* Patent Summary */}
        {Object.keys(patentSummary).length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {patentSummary.total_patents !== undefined && (
              <div className="bg-gray-800/30 rounded-lg p-3 border border-gray-800">
                <div className="flex items-center gap-2 mb-1">
                  <FileText className="w-4 h-4 text-purple-400" />
                  <span className="text-xs text-gray-500 uppercase">Total</span>
                </div>
                <p className="text-lg font-semibold text-white">{patentSummary.total_patents}</p>
              </div>
            )}
            {patentSummary.granted !== undefined && (
              <div className="bg-gray-800/30 rounded-lg p-3 border border-gray-800">
                <div className="flex items-center gap-2 mb-1">
                  <Calendar className="w-4 h-4 text-green-400" />
                  <span className="text-xs text-gray-500 uppercase">Granted</span>
                </div>
                <p className="text-lg font-semibold text-white">{patentSummary.granted}</p>
              </div>
            )}
            {patentSummary.pending !== undefined && (
              <div className="bg-gray-800/30 rounded-lg p-3 border border-gray-800">
                <div className="flex items-center gap-2 mb-1">
                  <Building2 className="w-4 h-4 text-yellow-400" />
                  <span className="text-xs text-gray-500 uppercase">Pending</span>
                </div>
                <p className="text-lg font-semibold text-white">{patentSummary.pending}</p>
              </div>
            )}
          </div>
        )}

        {/* Patent Heatmap Placeholder */}
        {patents.length > 0 && (
          <div className="bg-gray-800/30 rounded-lg p-4 border border-gray-800">
            <h4 className="text-xs font-semibold text-gray-400 mb-3 uppercase tracking-wider">
              Patent Activity Heatmap
            </h4>
            <div className="text-xs text-gray-500 italic">
              Heatmap visualization coming soon. {patents.length} patent{patents.length !== 1 ? "s" : ""} found.
            </div>
          </div>
        )}

        {/* Patents Table */}
        {patents.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
              Patent Details
            </h4>
            <div className="border border-gray-800 rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-gray-800/50 border-gray-800">
                    <TableHead className="text-gray-300 text-xs">Patent Number</TableHead>
                    <TableHead className="text-gray-300 text-xs">Title</TableHead>
                    <TableHead className="text-gray-300 text-xs">Assignee</TableHead>
                    <TableHead className="text-gray-300 text-xs">Status</TableHead>
                    <TableHead className="text-gray-300 text-xs">Filing Date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {patents.slice(0, 10).map((patent, idx) => (
                    <TableRow key={idx} className="border-gray-800 hover:bg-gray-800/30">
                      <TableCell className="text-gray-300 text-xs">
                        {patent.patent_number || "N/A"}
                      </TableCell>
                      <TableCell className="text-gray-300 text-xs max-w-xs truncate">
                        {patent.title || "N/A"}
                      </TableCell>
                      <TableCell className="text-gray-300 text-xs">
                        {patent.assignee || "N/A"}
                      </TableCell>
                      <TableCell>
                        {patent.status ? (
                          <Badge className={`${getStatusColor(patent.status)} border text-xs`}>
                            {patent.status}
                          </Badge>
                        ) : (
                          <span className="text-xs text-gray-500">N/A</span>
                        )}
                      </TableCell>
                      <TableCell className="text-gray-300 text-xs">
                        {patent.filing_date || "N/A"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            {patents.length > 10 && (
              <p className="text-xs text-gray-500 mt-2">
                Showing 10 of {patents.length} patents
              </p>
            )}
          </div>
        )}

        {/* Key Assignees */}
        {patentSummary.key_assignees && patentSummary.key_assignees.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
              Key Assignees
            </h4>
            <div className="flex flex-wrap gap-2">
              {patentSummary.key_assignees.map((assignee, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 bg-gray-800/50 border border-gray-700 rounded text-xs text-gray-300"
                >
                  {assignee}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </AgentSection>
  );
}

