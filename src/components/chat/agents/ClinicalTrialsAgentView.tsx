import React from "react";
import { FlaskConical, Calendar, Users } from "lucide-react";
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

type ClinicalTrialsAgentData = {
  section: string;
  summary: string;
  details?: {
    trials?: Array<{
      nct_id?: string;
      title?: string;
      phase?: string;
      status?: string;
      enrollment?: string;
      completion_date?: string;
      conditions?: string[];
      interventions?: string[];
      locations?: string[];
      results_link?: string;
    }>;
    trial_summary?: {
      total_trials?: number;
      active_trials?: number;
      completed_trials?: number;
      phases?: Record<string, number>;
    };
    [key: string]: any;
  };
  confidence?: number;
  sources?: string[];
};

export default function ClinicalTrialsAgentView({
  worker,
}: {
  worker: ClinicalTrialsAgentData;
}) {
  const details = worker.details || {};
  const trials = details.trials || details.external_trials || [];
  const trialSummary = details.trial_summary || {};

  const getPhaseColor = (phase?: string) => {
    if (!phase) return "bg-gray-500/20 text-gray-400";
    const p = phase.toLowerCase();
    if (p.includes("i")) return "bg-blue-500/20 text-blue-400";
    if (p.includes("ii")) return "bg-green-500/20 text-green-400";
    if (p.includes("iii")) return "bg-purple-500/20 text-purple-400";
    if (p.includes("iv")) return "bg-orange-500/20 text-orange-400";
    return "bg-gray-500/20 text-gray-400";
  };

  const getStatusColor = (status?: string) => {
    if (!status) return "bg-gray-500/20 text-gray-400";
    const s = status.toLowerCase();
    if (s.includes("recruiting") || s.includes("active")) return "bg-green-500/20 text-green-400";
    if (s.includes("completed")) return "bg-blue-500/20 text-blue-400";
    if (s.includes("terminated") || s.includes("suspended")) return "bg-red-500/20 text-red-400";
    return "bg-gray-500/20 text-gray-400";
  };

  return (
    <AgentSection
      title="Clinical Trials"
      icon={<FlaskConical className="w-5 h-5" />}
      summary={worker.summary}
      confidence={worker.confidence}
      sources={worker.sources}
      color="blue"
    >
      <div className="space-y-4">
        {/* Trial Summary */}
        {Object.keys(trialSummary).length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {trialSummary.total_trials !== undefined && (
              <div className="bg-gray-800/30 rounded-lg p-3 border border-gray-800">
                <div className="flex items-center gap-2 mb-1">
                  <FlaskConical className="w-4 h-4 text-blue-400" />
                  <span className="text-xs text-gray-500 uppercase">Total</span>
                </div>
                <p className="text-lg font-semibold text-white">{trialSummary.total_trials}</p>
              </div>
            )}
            {trialSummary.active_trials !== undefined && (
              <div className="bg-gray-800/30 rounded-lg p-3 border border-gray-800">
                <div className="flex items-center gap-2 mb-1">
                  <Calendar className="w-4 h-4 text-green-400" />
                  <span className="text-xs text-gray-500 uppercase">Active</span>
                </div>
                <p className="text-lg font-semibold text-white">{trialSummary.active_trials}</p>
              </div>
            )}
            {trialSummary.completed_trials !== undefined && (
              <div className="bg-gray-800/30 rounded-lg p-3 border border-gray-800">
                <div className="flex items-center gap-2 mb-1">
                  <Users className="w-4 h-4 text-purple-400" />
                  <span className="text-xs text-gray-500 uppercase">Completed</span>
                </div>
                <p className="text-lg font-semibold text-white">{trialSummary.completed_trials}</p>
              </div>
            )}
          </div>
        )}

        {/* Trials Table */}
        {trials.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
              Trial Details
            </h4>
            <div className="border border-gray-800 rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-gray-800/50 border-gray-800">
                    <TableHead className="text-gray-300 text-xs">NCT ID</TableHead>
                    <TableHead className="text-gray-300 text-xs">Title</TableHead>
                    <TableHead className="text-gray-300 text-xs">Phase</TableHead>
                    <TableHead className="text-gray-300 text-xs">Status</TableHead>
                    <TableHead className="text-gray-300 text-xs">Enrollment</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {trials.slice(0, 10).map((trial, idx) => (
                    <TableRow key={idx} className="border-gray-800 hover:bg-gray-800/30">
                      <TableCell className="text-gray-300 text-xs">
                        {trial.nct_id ? (
                          <a
                            href={`https://clinicaltrials.gov/ct2/show/${trial.nct_id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-400 hover:text-blue-300"
                          >
                            {trial.nct_id}
                          </a>
                        ) : (
                          "N/A"
                        )}
                      </TableCell>
                      <TableCell className="text-gray-300 text-xs max-w-xs truncate">
                        {trial.title || "N/A"}
                      </TableCell>
                      <TableCell>
                        {trial.phase ? (
                          <Badge className={`${getPhaseColor(trial.phase)} border text-xs`}>
                            {trial.phase}
                          </Badge>
                        ) : (
                          <span className="text-xs text-gray-500">N/A</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {trial.status ? (
                          <Badge className={`${getStatusColor(trial.status)} border text-xs`}>
                            {trial.status}
                          </Badge>
                        ) : (
                          <span className="text-xs text-gray-500">N/A</span>
                        )}
                      </TableCell>
                      <TableCell className="text-gray-300 text-xs">
                        {trial.enrollment || "N/A"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            {trials.length > 10 && (
              <p className="text-xs text-gray-500 mt-2">
                Showing 10 of {trials.length} trials
              </p>
            )}
          </div>
        )}

        {/* Additional Details */}
        {Object.keys(details).length > 0 && !trials.length && (
          <div>
            <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
              Insights
            </h4>
            <div className="text-sm text-gray-300 space-y-1">
              {Object.entries(details).map(([key, value]) => {
                if (["trials", "external_trials", "trial_summary"].includes(key)) {
                  return null;
                }
                if (typeof value === "string") {
                  return (
                    <div key={key}>
                      <span className="text-gray-500 capitalize">{key.replace(/_/g, " ")}:</span>{" "}
                      <span>{value}</span>
                    </div>
                  );
                }
                if (Array.isArray(value) && value.length > 0) {
                  return (
                    <div key={key}>
                      <span className="text-gray-500 capitalize">{key.replace(/_/g, " ")}:</span>
                      <ul className="ml-4 mt-1 space-y-1">
                        {value.map((item, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-blue-400 mt-1">•</span>
                            <span>{typeof item === "string" ? item : JSON.stringify(item)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  );
                }
                return null;
              })}
            </div>
          </div>
        )}
      </div>
    </AgentSection>
  );
}

