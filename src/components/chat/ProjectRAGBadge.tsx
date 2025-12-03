import React, { useState, useEffect } from "react";
import { Database, AlertCircle, CheckCircle } from "lucide-react";
import { api, RAGStatus } from "@/lib/api";

interface ProjectRAGBadgeProps {
  projectId?: string | null;
  projectName?: string;
}

export default function ProjectRAGBadge({ projectId, projectName }: ProjectRAGBadgeProps) {
  const [ragStatus, setRagStatus] = useState<RAGStatus | null>(null);
  const [fileCount, setFileCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showTooltip, setShowTooltip] = useState(false);

  useEffect(() => {
    if (!projectId) {
      setLoading(false);
      return;
    }

    const loadStatus = async () => {
      try {
        const [status, filesRes] = await Promise.all([
          api.projectFiles.getRagStatus(),
          api.projectFiles.list(projectId),
        ]);
        setRagStatus(status);
        setFileCount(filesRes.total);
      } catch (error) {
        console.error("Failed to load RAG status:", error);
      } finally {
        setLoading(false);
      }
    };

    loadStatus();
  }, [projectId]);

  if (!projectId) {
    return null;
  }

  if (loading) {
    return (
      <div className="flex items-center gap-1.5 px-2 py-1 bg-gray-800/50 rounded text-xs text-gray-400">
        <Database className="w-3 h-3 animate-pulse" />
        Loading...
      </div>
    );
  }

  const ragEnabled = ragStatus?.project_rag?.enabled ?? false;

  return (
    <div className="relative inline-block">
      <div
        className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs cursor-help transition-colors ${
          ragEnabled
            ? "bg-green-500/10 text-green-400 border border-green-500/30"
            : "bg-gray-800/50 text-gray-400 border border-gray-700"
        }`}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        {ragEnabled ? (
          <CheckCircle className="w-3 h-3" />
        ) : (
          <AlertCircle className="w-3 h-3" />
        )}
        <span>📘 Project Knowledge</span>
        {ragEnabled ? (
          <span className="text-green-300 font-medium">{fileCount} docs</span>
        ) : (
          <span className="text-gray-500">(Disabled)</span>
        )}
      </div>

      {showTooltip && (
        <div className="absolute top-full left-0 mt-2 z-50 w-72 p-3 bg-gray-900 border border-gray-700 rounded-lg shadow-xl">
          <div className="font-medium text-white flex items-center gap-2 mb-2">
            <Database className="w-4 h-4 text-blue-400" />
            Project RAG System
          </div>
          {ragEnabled ? (
            <>
              <p className="text-sm text-green-400 mb-1">✓ RAG retrieval is active</p>
              <p className="text-xs text-gray-400">
                {fileCount} documents indexed. Relevant content will enhance responses.
              </p>
            </>
          ) : (
            <>
              <p className="text-sm text-amber-400 mb-1">⚠️ RAG Disabled — Model Too Small</p>
              <p className="text-xs text-gray-400">
                {fileCount} documents stored. RAG requires larger models (≥14B/70B).
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Current: {ragStatus?.current_model || "Unknown"}
              </p>
            </>
          )}
          {projectName && (
            <p className="text-xs text-gray-500 pt-2 mt-2 border-t border-gray-700">
              Project: {projectName}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
