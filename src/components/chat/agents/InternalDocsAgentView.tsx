import React from "react";
import { FileText, Database, Search } from "lucide-react";
import AgentSection from "./AgentSection";

type InternalDocsAgentData = {
  section: string;
  summary: string;
  details?: {
    internal_docs?: Array<{
      document_id?: string;
      title?: string;
      type?: string;
      relevance?: number;
      snippet?: string;
      metadata?: Record<string, any>;
    }>;
    documents_found?: number;
    [key: string]: any;
  };
  confidence?: number;
  sources?: string[];
};

export default function InternalDocsAgentView({ worker }: { worker: InternalDocsAgentData }) {
  const details = worker.details || {};
  const internalDocs = details.internal_docs || [];
  const documentsFound = details.documents_found;

  return (
    <AgentSection
      title="Internal Documents"
      icon={<Database className="w-5 h-5" />}
      summary={worker.summary}
      confidence={worker.confidence}
      sources={worker.sources}
      color="cyan"
    >
      <div className="space-y-4">
        {/* Documents Found Count */}
        {documentsFound !== undefined && (
          <div className="bg-gray-800/30 rounded-lg p-3 border border-gray-800">
            <div className="flex items-center gap-2">
              <Search className="w-4 h-4 text-cyan-400" />
              <span className="text-sm text-gray-300">
                Found {documentsFound} internal document{documentsFound !== 1 ? "s" : ""}
              </span>
            </div>
          </div>
        )}

        {/* Internal Documents List */}
        {internalDocs.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
              Relevant Documents
            </h4>
            <div className="space-y-2">
              {internalDocs.map((doc, idx) => (
                <div
                  key={idx}
                  className="bg-gray-800/30 rounded-lg p-3 border border-gray-800"
                >
                  <div className="flex items-start gap-2">
                    <FileText className="w-4 h-4 text-cyan-400 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <h5 className="text-sm font-medium text-white mb-1">
                        {doc.title || doc.document_id || `Document ${idx + 1}`}
                      </h5>
                      {doc.type && (
                        <span className="text-xs text-gray-500 mb-2 inline-block">
                          Type: {doc.type}
                        </span>
                      )}
                      {doc.snippet && (
                        <p className="text-xs text-gray-400 line-clamp-2 mt-1">{doc.snippet}</p>
                      )}
                      <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                        {doc.document_id && <span>ID: {doc.document_id}</span>}
                        {doc.relevance !== undefined && (
                          <span>Relevance: {doc.relevance}%</span>
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

