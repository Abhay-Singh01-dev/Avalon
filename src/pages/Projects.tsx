import React from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Plus,
  FolderOpen,
  Calendar,
  MessageSquare,
  ChevronRight,
  Edit3,
  Trash2,
  MoreVertical,
  Upload,
  FileText,
  Database,
  X,
} from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAppContext } from "@/context/AppContext";
import { api } from "@/lib/api";
import { useNavigate } from "react-router-dom";
import { formatDistanceToNow } from "date-fns";
import { Switch } from "@/components/ui/switch";

interface ProjectFile {
  id: string;
  name: string;
  fileName: string;
  size: string;
  uploadedAt: string;
  enabled: boolean;
}

// Store project files in memory (would be persisted to backend in production)
const projectFilesStore: Record<string, ProjectFile[]> = {};

const colorGradients = [
  "from-blue-500 to-cyan-500",
  "from-purple-500 to-pink-500",
  "from-green-500 to-emerald-500",
  "from-orange-500 to-red-500",
  "from-indigo-500 to-blue-500",
  "from-pink-500 to-rose-500",
];

function ProjectCard({ project, colorGradient }) {
  const { chats, selectConversation, refreshProjects } = useAppContext();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = React.useState(false);
  const [renameOpen, setRenameOpen] = React.useState(false);
  const [deleteOpen, setDeleteOpen] = React.useState(false);
  const [newName, setNewName] = React.useState(project.name);
  
  // Project files state for RAG
  const [projectFiles, setProjectFiles] = React.useState<ProjectFile[]>(
    () => projectFilesStore[project.id] || []
  );

  // Sync files to store when they change
  React.useEffect(() => {
    projectFilesStore[project.id] = projectFiles;
  }, [projectFiles, project.id]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const newFile: ProjectFile = {
      id: Date.now().toString(),
      name: file.name.replace(/\.[^/.]+$/, ""),
      fileName: file.name,
      size: formatFileSize(file.size),
      uploadedAt: new Date().toISOString(),
      enabled: true,
    };
    setProjectFiles(prev => [...prev, newFile]);
    e.target.value = '';
  };

  const removeFile = (fileId: string) => {
    setProjectFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const toggleFileEnabled = (fileId: string) => {
    setProjectFiles(prev => 
      prev.map(f => f.id === fileId ? { ...f, enabled: !f.enabled } : f)
    );
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Get chats for this project
  const projectChats = React.useMemo(() => {
    if (!project.chat_ids || project.chat_ids.length === 0) return [];
    return chats
      .filter((chat) => project.chat_ids?.includes(chat.id))
      .sort((a, b) => {
        const dateA = a.updated_at ? new Date(a.updated_at).getTime() : 0;
        const dateB = b.updated_at ? new Date(b.updated_at).getTime() : 0;
        return dateB - dateA;
      });
  }, [chats, project.chat_ids]);

  const handleOpenChat = async (chatId: string) => {
    console.log("[Projects] Opening chat:", chatId);
    try {
      await selectConversation(chatId);
      navigate(`/chat/${chatId}`);
      console.log("[Projects] Navigated to chat:", chatId);
    } catch (error) {
      console.error("[Projects] Failed to open chat:", error);
    }
  };

  const handleRename = async () => {
    if (!newName.trim()) return;
    try {
      await api.projects.rename(project.id, { name: newName });
      await refreshProjects();
      setRenameOpen(false);
    } catch (error) {
      console.error("Failed to rename project:", error);
    }
  };

  const handleDelete = async () => {
    try {
      await api.projects.remove(project.id);
      await refreshProjects();
      setDeleteOpen(false);
    } catch (error) {
      console.error("Failed to delete project:", error);
    }
  };

  const lastUpdated = project.updated_at
    ? formatDistanceToNow(new Date(project.updated_at), { addSuffix: true })
    : "Never";

  return (
    <>
      <Card className="bg-gray-900/40 border-gray-800/50 hover:border-gray-700/50 transition-all">
        <Collapsible open={isOpen} onOpenChange={setIsOpen}>
          <div className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div
                className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorGradient} flex items-center justify-center shadow-lg`}
              >
                <FolderOpen className="w-6 h-6 text-white" />
              </div>
              <div className="flex items-center gap-2">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-gray-400 hover:text-gray-200 hover:bg-gray-800/50"
                    >
                      <MoreVertical className="w-4 h-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent
                    align="end"
                    className="bg-gray-950/80 border-gray-800/50 text-gray-200"
                  >
                    <DropdownMenuItem
                      onClick={() => {
                        setNewName(project.name);
                        setRenameOpen(true);
                      }}
                      className="hover:bg-gray-800 cursor-pointer"
                    >
                      <Edit3 className="w-4 h-4 mr-2 text-blue-500" />
                      Rename
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => setDeleteOpen(true)}
                      className="hover:bg-gray-800 cursor-pointer text-red-400"
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
                <CollapsibleTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-gray-400 hover:text-cyan-400 hover:bg-cyan-500/10"
                  >
                    <ChevronRight
                      className={`w-4 h-4 transition-transform duration-200 ${
                        isOpen ? "rotate-90" : ""
                      }`}
                    />
                  </Button>
                </CollapsibleTrigger>
              </div>
            </div>

            <h3 className="text-lg font-semibold text-white mb-2 hover:text-cyan-400 transition-colors cursor-pointer">
              {project.name}
            </h3>
            <p className="text-sm text-gray-500 mb-4 line-clamp-2">
              {project.description || "No description"}
            </p>

            <div className="flex items-center justify-between text-xs text-gray-600">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-1">
                  <MessageSquare className="w-3 h-3" />
                  <span>{projectChats.length} chats</span>
                </div>
                <div className="flex items-center gap-1">
                  <Database className="w-3 h-3" />
                  <span>{projectFiles.length} files</span>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                <span>{lastUpdated}</span>
              </div>
            </div>
          </div>

          <CollapsibleContent>
            <div className="border-t border-gray-800 px-6 py-4 bg-black/30 space-y-4">
              {/* Knowledge Base Section */}
              <div>
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <Database className="w-3 h-3 text-amber-500" />
                  Knowledge Base (RAG)
                </h4>
                <p className="text-xs text-gray-600 mb-3">
                  Upload files for this project. They will be used as context for all chats in this project.
                </p>
                
                {/* Uploaded Files */}
                {projectFiles.length > 0 && (
                  <div className="space-y-2 mb-3">
                    {projectFiles.map((file) => (
                      <div
                        key={file.id}
                        className="flex items-center gap-2 p-2 bg-gray-900/50 rounded-lg border border-gray-800/50 group"
                      >
                        <Switch
                          checked={file.enabled}
                          onCheckedChange={() => toggleFileEnabled(file.id)}
                          className="scale-75"
                        />
                        <FileText className="w-4 h-4 text-amber-400 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <span className="text-xs text-gray-300 block truncate">{file.name}</span>
                          <span className="text-xs text-gray-600">{file.size} • {formatDistanceToNow(new Date(file.uploadedAt), { addSuffix: true })}</span>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => removeFile(file.id)}
                          className="h-6 w-6 text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <X className="w-3 h-3" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Upload Button */}
                <label className="flex items-center gap-2 p-3 border border-dashed border-gray-700 rounded-lg cursor-pointer hover:border-amber-500/50 hover:bg-amber-500/5 transition-all">
                  <Upload className="w-4 h-4 text-gray-400" />
                  <span className="text-xs text-gray-400">Upload Documents (PDF, DOCX, TXT)</span>
                  <input
                    type="file"
                    accept=".pdf,.docx,.doc,.txt,.md"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </label>
              </div>

              {/* Chats Section */}
              <div>
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                  Chats
                </h4>
                {projectChats.length > 0 ? (
                  <div className="space-y-2">
                    {projectChats.map((chat) => (
                      <div
                        key={chat.id}
                        onClick={() => handleOpenChat(chat.id)}
                        className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-800/50 cursor-pointer transition-colors group"
                      >
                        <div className="flex items-center gap-2 flex-1">
                          <MessageSquare className="w-3 h-3 text-blue-500/50 group-hover:text-blue-400" />
                          <span className="text-sm text-gray-400 group-hover:text-gray-200 truncate">
                            {chat.title}
                          </span>
                        </div>
                        <span className="text-xs text-gray-600">
                          {chat.updated_at
                            ? formatDistanceToNow(new Date(chat.updated_at), {
                                addSuffix: true,
                              })
                            : "N/A"}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-600">
                    No chats in this project
                  </p>
                )}
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </Card>

      {/* Rename Dialog */}
      <Dialog open={renameOpen} onOpenChange={setRenameOpen}>
        <DialogContent className="bg-gray-900 border-gray-800 text-gray-200">
          <DialogHeader>
            <DialogTitle className="text-xl font-semibold text-white">
              Rename Project
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label htmlFor="project-name" className="text-gray-300">
                Project Name
              </Label>
              <Input
                id="project-name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Enter project name"
                className="bg-black border-gray-800 text-gray-300"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    handleRename();
                  }
                }}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button
                variant="ghost"
                onClick={() => setRenameOpen(false)}
                className="text-gray-400 hover:text-gray-200"
              >
                Cancel
              </Button>
              <Button
                onClick={handleRename}
                className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500"
                disabled={!newName.trim()}
              >
                Save
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Dialog */}
      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent className="bg-gray-900 border-gray-800 text-gray-200">
          <DialogHeader>
            <DialogTitle className="text-xl font-semibold text-white">
              Delete Project
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <p className="text-gray-400">
              Are you sure you want to delete "{project.name}"? This action
              cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <Button
                variant="ghost"
                onClick={() => setDeleteOpen(false)}
                className="text-gray-400 hover:text-gray-200"
              >
                Cancel
              </Button>
              <Button
                onClick={handleDelete}
                className="bg-red-600 hover:bg-red-500 text-white"
              >
                Delete
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

export default function ProjectsPage() {
  const { projects, refreshProjects, loading } = useAppContext();
  const [createOpen, setCreateOpen] = React.useState(false);
  const [newProjectName, setNewProjectName] = React.useState("");
  const [newProjectDesc, setNewProjectDesc] = React.useState("");

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return;
    try {
      await api.projects.create({
        name: newProjectName,
        description: newProjectDesc || undefined,
      });
      await refreshProjects();
      setCreateOpen(false);
      setNewProjectName("");
      setNewProjectDesc("");
    } catch (error) {
      console.error("Failed to create project:", error);
    }
  };

  return (
    <div className="flex flex-col h-full bg-black overflow-auto">
      <div className="max-w-6xl mx-auto w-full p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Projects</h1>
            <p className="text-gray-500">
              Organize your research into focused workspaces
            </p>
          </div>
          <Button
            onClick={() => setCreateOpen(true)}
            className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 shadow-lg shadow-blue-500/20"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Project
          </Button>
        </div>

        {loading ? (
          <div className="text-center py-20">
            <FolderOpen className="w-12 h-12 text-gray-700 mx-auto mb-4 animate-pulse" />
            <p className="text-gray-500">Loading projects...</p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project, index) => (
              <ProjectCard
                key={project.id}
                project={project}
                colorGradient={colorGradients[index % colorGradients.length]}
              />
            ))}

            {/* Create New Project Card */}
            <Card
              onClick={() => setCreateOpen(true)}
              className="bg-gray-900/30 border-2 border-dashed border-gray-800 p-6 hover:border-cyan-500/50 transition-all cursor-pointer group flex items-center justify-center min-h-[200px]"
            >
              <div className="text-center">
                <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-gray-800 group-hover:bg-cyan-500/20 flex items-center justify-center transition-colors">
                  <Plus className="w-6 h-6 text-gray-600 group-hover:text-cyan-400 transition-colors" />
                </div>
                <h3 className="text-sm font-medium text-gray-500 group-hover:text-cyan-400 transition-colors">
                  Create New Project
                </h3>
              </div>
            </Card>
          </div>
        )}
      </div>

      {/* Create Project Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="bg-gray-900 border-gray-800 text-gray-200">
          <DialogHeader>
            <DialogTitle className="text-xl font-semibold text-white">
              Create New Project
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label htmlFor="project-name" className="text-gray-300">
                Project Name
              </Label>
              <Input
                id="project-name"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                placeholder="Enter project name"
                className="bg-black border-gray-800 text-gray-300"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    handleCreateProject();
                  }
                }}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="project-desc" className="text-gray-300">
                Description (Optional)
              </Label>
              <Input
                id="project-desc"
                value={newProjectDesc}
                onChange={(e) => setNewProjectDesc(e.target.value)}
                placeholder="Enter project description"
                className="bg-black border-gray-800 text-gray-300"
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button
                variant="ghost"
                onClick={() => {
                  setCreateOpen(false);
                  setNewProjectName("");
                  setNewProjectDesc("");
                }}
                className="text-gray-400 hover:text-gray-200"
              >
                Cancel
              </Button>
              <Button
                onClick={handleCreateProject}
                className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500"
                disabled={!newProjectName.trim()}
              >
                Create
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
