import React, { useState, useEffect, useCallback } from "react";
import { 
  Upload, 
  FileText, 
  Trash2, 
  Eye, 
  RefreshCw, 
  Link as LinkIcon,
  Plus,
  X,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle,
  Database,
  Info
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { api, ProjectFile, ProjectLink, RAGStatus } from "@/lib/api";

interface ProjectFilesManagerProps {
  projectId: string;
  projectName?: string;
}

export default function ProjectFilesManager({ projectId, projectName }: ProjectFilesManagerProps) {
  const [files, setFiles] = useState<ProjectFile[]>([]);
  const [links, setLinks] = useState<ProjectLink[]>([]);
  const [ragStatus, setRagStatus] = useState<RAGStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  
  // Link form
  const [showAddLink, setShowAddLink] = useState(false);
  const [newLinkUrl, setNewLinkUrl] = useState("");
  const [newLinkTitle, setNewLinkTitle] = useState("");
  const [addingLink, setAddingLink] = useState(false);
  
  // Preview modal
  const [previewFile, setPreviewFile] = useState<{
    id: string;
    filename: string;
    extracted_text: string;
    chunk_count: number;
  } | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [filesRes, linksRes, statusRes] = await Promise.all([
        api.projectFiles.list(projectId),
        api.projectLinks.list(projectId),
        api.projectFiles.getRagStatus(),
      ]);
      setFiles(filesRes.files);
      setLinks(linksRes.links);
      setRagStatus(statusRes);
    } catch (error) {
      console.error("Failed to load project data:", error);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      await api.projectFiles.upload(projectId, file);
      await loadData();
    } catch (error) {
      console.error("Failed to upload file:", error);
      alert(`Upload failed: ${(error as Error).message}`);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleDeleteFile = async (fileId: string) => {
    if (!confirm("Are you sure you want to delete this file?")) return;
    
    try {
      await api.projectFiles.delete(projectId, fileId);
      setFiles(files.filter(f => f.id !== fileId));
    } catch (error) {
      console.error("Failed to delete file:", error);
    }
  };

  const handlePreviewFile = async (fileId: string) => {
    try {
      const preview = await api.projectFiles.preview(projectId, fileId);
      setPreviewFile(preview);
    } catch (error) {
      console.error("Failed to load preview:", error);
    }
  };

  const handleReindex = async () => {
    try {
      setReindexing(true);
      const result = await api.projectFiles.reindex(projectId);
      alert(result.message);
      await loadData();
    } catch (error) {
      console.error("Failed to reindex:", error);
    } finally {
      setReindexing(false);
    }
  };

  const handleAddLink = async () => {
    if (!newLinkUrl.trim()) return;
    
    try {
      setAddingLink(true);
      await api.projectLinks.add(projectId, {
        url: newLinkUrl.trim(),
        title: newLinkTitle.trim() || undefined,
      });
      setNewLinkUrl("");
      setNewLinkTitle("");
      setShowAddLink(false);
      await loadData();
    } catch (error) {
      console.error("Failed to add link:", error);
      alert(`Failed to add link: ${(error as Error).message}`);
    } finally {
      setAddingLink(false);
    }
  };

  const handleDeleteLink = async (linkId: string) => {
    try {
      await api.projectLinks.delete(projectId, linkId);
      setLinks(links.filter(l => l.id !== linkId));
    } catch (error) {
      console.error("Failed to delete link:", error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'indexed':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'processing':
        return <Clock className="w-4 h-4 text-yellow-400 animate-pulse" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-400" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const ragEnabled = ragStatus?.project_rag?.enabled ?? false;

  return (
    <div className="space-y-6">
      {/* RAG Status Banner */}
      <div className={`p-4 rounded-lg border ${
        ragEnabled 
          ? 'bg-green-500/10 border-green-500/30' 
          : 'bg-gray-800/50 border-gray-700'
      }`}>
        <div className="flex items-start gap-3">
          <Database className={`w-5 h-5 mt-0.5 ${ragEnabled ? 'text-green-400' : 'text-gray-400'}`} />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className={`font-medium ${ragEnabled ? 'text-green-400' : 'text-gray-300'}`}>
                📘 Project Knowledge Base
              </h3>
              <span className={`text-xs px-2 py-0.5 rounded ${
                ragEnabled 
                  ? 'bg-green-500/20 text-green-400' 
                  : 'bg-gray-700 text-gray-400'
              }`}>
                {ragEnabled ? 'Enabled' : 'Disabled — Model Too Small'}
              </span>
            </div>
            <p className="text-sm text-gray-400 mt-1">
              {ragEnabled 
                ? `${files.length} documents loaded • RAG retrieval active`
                : 'Documents are stored and indexed, but RAG retrieval requires larger models (≥14B/70B).'
              }
            </p>
            {!ragEnabled && (
              <p className="text-xs text-amber-400/80 mt-2 flex items-center gap-1">
                <Info className="w-3 h-3" />
                Current model: {ragStatus?.current_model || 'Unknown'} — Upgrade to enable RAG
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Files Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-200 flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-400" />
            Documents ({files.length})
          </h3>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleReindex}
              disabled={reindexing || files.length === 0}
              className="text-gray-400 hover:text-gray-200"
              title={!ragEnabled ? "Re-index available, but embeddings require larger model" : "Re-index all documents"}
            >
              <RefreshCw className={`w-4 h-4 mr-1 ${reindexing ? 'animate-spin' : ''}`} />
              Re-index
            </Button>
            <label className="cursor-pointer">
              <Button
                variant="outline"
                size="sm"
                disabled={uploading}
                className="border-blue-500/30 text-blue-400 hover:bg-blue-500/10"
                asChild
              >
                <span>
                  <Upload className={`w-4 h-4 mr-1 ${uploading ? 'animate-pulse' : ''}`} />
                  {uploading ? 'Uploading...' : 'Upload Document'}
                </span>
              </Button>
              <input
                type="file"
                className="hidden"
                accept=".pdf,.docx,.txt,.csv,.xlsx"
                onChange={handleFileUpload}
                disabled={uploading}
              />
            </label>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-400">Loading...</div>
        ) : files.length === 0 ? (
          <div className="text-center py-8 border border-dashed border-gray-700 rounded-lg">
            <FileText className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No documents uploaded yet</p>
            <p className="text-sm text-gray-500 mt-1">
              Upload PDF, DOCX, TXT, CSV, or XLSX files
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {files.map((file) => (
              <div
                key={file.id}
                className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg border border-gray-700/50 hover:border-gray-600 transition-colors"
              >
                <div className="flex items-center gap-3">
                  {getStatusIcon(file.status)}
                  <div>
                    <p className="text-sm font-medium text-gray-200">
                      {file.original_filename}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatFileSize(file.file_size)} • {file.chunk_count || 0} chunks
                      {file.status === 'failed' && file.error && (
                        <span className="text-red-400 ml-2">Error: {file.error}</span>
                      )}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handlePreviewFile(file.id)}
                    className="text-gray-400 hover:text-gray-200"
                  >
                    <Eye className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteFile(file.id)}
                    className="text-gray-400 hover:text-red-400"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Links Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-200 flex items-center gap-2">
            <LinkIcon className="w-5 h-5 text-purple-400" />
            Saved Links ({links.length})
          </h3>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAddLink(true)}
            className="border-purple-500/30 text-purple-400 hover:bg-purple-500/10"
          >
            <Plus className="w-4 h-4 mr-1" />
            Add Link
          </Button>
        </div>

        {!ragStatus?.link_fetch?.enabled && (
          <div className="text-xs text-amber-400/80 flex items-center gap-1 p-2 bg-amber-500/10 rounded border border-amber-500/20">
            <AlertCircle className="w-3 h-3" />
            Link fetching is disabled. URLs are saved for future use when larger models are available.
          </div>
        )}

        {links.length === 0 ? (
          <div className="text-center py-6 border border-dashed border-gray-700 rounded-lg">
            <LinkIcon className="w-10 h-10 text-gray-600 mx-auto mb-2" />
            <p className="text-gray-400 text-sm">No links saved yet</p>
          </div>
        ) : (
          <div className="space-y-2">
            {links.map((link) => (
              <div
                key={link.id}
                className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg border border-gray-700/50"
              >
                <div className="flex items-center gap-3">
                  <LinkIcon className="w-4 h-4 text-gray-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-200">
                      {link.title || link.url}
                    </p>
                    <p className="text-xs text-gray-500 truncate max-w-md">
                      {link.url}
                    </p>
                    <span className="text-xs text-amber-400/70">
                      🔗 Saved (fetch disabled for small models)
                    </span>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDeleteLink(link.id)}
                  className="text-gray-400 hover:text-red-400"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Link Dialog */}
      <Dialog open={showAddLink} onOpenChange={setShowAddLink}>
        <DialogContent className="bg-gray-900 border-gray-800 text-gray-200">
          <DialogHeader>
            <DialogTitle className="text-white">Add Link</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <label className="text-sm text-gray-400 mb-1 block">URL *</label>
              <Input
                value={newLinkUrl}
                onChange={(e) => setNewLinkUrl(e.target.value)}
                placeholder="https://example.com/article"
                className="bg-gray-800 border-gray-700"
              />
            </div>
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Title (optional)</label>
              <Input
                value={newLinkTitle}
                onChange={(e) => setNewLinkTitle(e.target.value)}
                placeholder="Article title"
                className="bg-gray-800 border-gray-700"
              />
            </div>
            <div className="text-xs text-amber-400/80 flex items-center gap-1">
              <Info className="w-3 h-3" />
              Link will be saved but not fetched. Fetching requires larger models.
            </div>
            <div className="flex justify-end gap-2">
              <Button
                variant="ghost"
                onClick={() => setShowAddLink(false)}
                className="text-gray-400"
              >
                Cancel
              </Button>
              <Button
                onClick={handleAddLink}
                disabled={!newLinkUrl.trim() || addingLink}
                className="bg-purple-600 hover:bg-purple-500"
              >
                {addingLink ? 'Adding...' : 'Add Link'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* File Preview Dialog */}
      <Dialog open={!!previewFile} onOpenChange={() => setPreviewFile(null)}>
        <DialogContent className="bg-gray-900 border-gray-800 text-gray-200 max-w-3xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center justify-between">
              <span>{previewFile?.filename}</span>
              <span className="text-sm font-normal text-gray-400">
                {previewFile?.chunk_count} chunks
              </span>
            </DialogTitle>
          </DialogHeader>
          <div className="mt-4 max-h-[60vh] overflow-y-auto">
            <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono bg-gray-800/50 p-4 rounded-lg">
              {previewFile?.extracted_text || 'No text extracted'}
            </pre>
          </div>
          <div className="flex justify-between items-center mt-4">
            <span className={`text-xs px-2 py-1 rounded ${
              ragEnabled ? 'bg-green-500/20 text-green-400' : 'bg-gray-700 text-gray-400'
            }`}>
              RAG: {ragEnabled ? 'Enabled' : 'Disabled'}
            </span>
            <Button
              variant="ghost"
              onClick={() => setPreviewFile(null)}
              className="text-gray-400"
            >
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
