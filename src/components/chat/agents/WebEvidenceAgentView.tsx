import React from "react";
import { Globe, ExternalLink, FileText } from "lucide-react";
import AgentSection from "./AgentSection";

type WebEvidenceAgentData = {
  section: string;
  summary: string;
  details?: {
    web_evidence?: Array<{
      title?: string;
      url?: string;
      source?: string;
      snippet?: string;
      relevance?: number;
      date?: string;
    }>;
    publications?: Array<{
      title?: string;
      authors?: string[];
      journal?: string;
      year?: number;
      doi?: string;
      url?: string;
    }>;
    [key: string]: any;
  };
  confidence?: number;
  sources?: string[];
};

export default function WebEvidenceAgentView({ worker }: { worker: WebEvidenceAgentData }) {
  const details = worker.details || {};
  const webEvidence = details.web_evidence || [];
  const publications = details.publications || [];

  return (
    <AgentSection
      title="Web Evidence"
      icon={<Globe className="w-5 h-5" />}
      summary={worker.summary}
      confidence={worker.confidence}
      sources={worker.sources}
      color="cyan"
    >
      <div className="space-y-4">
        {/* Web Evidence List */}
        {webEvidence.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
              Web Sources
            </h4>
            <div className="space-y-2">
              {webEvidence.map((evidence, idx) => (
                <div
                  key={idx}
                  className="bg-gray-800/30 rounded-lg p-3 border border-gray-800 hover:border-gray-700 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      {evidence.url ? (
                        <a
                          href={evidence.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm font-medium text-blue-400 hover:text-blue-300 flex items-center gap-1 mb-1"
                        >
                          {evidence.title || evidence.url}
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      ) : (
                        <h5 className="text-sm font-medium text-white mb-1">
                          {evidence.title || `Source ${idx + 1}`}
                        </h5>
                      )}
                      {evidence.snippet && (
                        <p className="text-xs text-gray-400 line-clamp-2">{evidence.snippet}</p>
                      )}
                      <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                        {evidence.source && <span>Source: {evidence.source}</span>}
                        {evidence.date && <span>Date: {evidence.date}</span>}
                        {evidence.relevance !== undefined && (
                          <span>Relevance: {evidence.relevance}%</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Publications List */}
        {publications.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
              Publications
            </h4>
            <div className="space-y-2">
              {publications.map((pub, idx) => (
                <div
                  key={idx}
                  className="bg-gray-800/30 rounded-lg p-3 border border-gray-800"
                >
                  <div className="flex items-start gap-2 mb-1">
                    <FileText className="w-4 h-4 text-cyan-400 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      {pub.url || pub.doi ? (
                        <a
                          href={pub.url || `https://doi.org/${pub.doi}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm font-medium text-blue-400 hover:text-blue-300 flex items-center gap-1"
                        >
                          {pub.title || "Untitled Publication"}
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      ) : (
                        <h5 className="text-sm font-medium text-white">
                          {pub.title || "Untitled Publication"}
                        </h5>
                      )}
                      <div className="text-xs text-gray-400 mt-1 space-y-0.5">
                        {pub.authors && pub.authors.length > 0 && (
                          <div>Authors: {pub.authors.join(", ")}</div>
                        )}
                        {pub.journal && <div>Journal: {pub.journal}</div>}
                        {pub.year && <div>Year: {pub.year}</div>}
                        {pub.doi && !pub.url && (
                          <div>
                            DOI:{" "}
                            <a
                              href={`https://doi.org/${pub.doi}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-400 hover:text-blue-300"
                            >
                              {pub.doi}
                            </a>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AgentSection>
  );
}

