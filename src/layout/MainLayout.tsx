import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { createPageUrl } from "@/lib/utils";
import {
  MessageSquare,
  Search,
  FileText,
  FolderOpen,
  Settings,
  Plus,
  Sparkles,
  ChevronRight,
  History,
  Menu,
  X,
  Shield,
  MoreVertical,
  Edit3,
  Trash2,
  FolderPlus,
  Check,
  Loader2,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import SearchChatsModal from "@/components/modals/SearchChatsModal";
import GroupChatModal from "@/components/modals/GroupChatModal";
import { useAppContext } from "@/context/AppContext";
import { api } from "@/lib/api";

export default function Layout({ children, currentPageName }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [projectsOpen, setProjectsOpen] = React.useState(true);
  const [chatsOpen, setChatsOpen] = React.useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false);
  const [logoHovered, setLogoHovered] = React.useState(false);
  const [searchModalOpen, setSearchModalOpen] = React.useState(false);
  const {
    chats,
    projects,
    createConversation,
    selectConversation,
    currentConversation,
    assignChatToProject,
    refreshAll,
    refreshChats,
    modals,
    setModalState,
    isCreatingChat,
  } = useAppContext();

  const [renameDialogOpen, setRenameDialogOpen] = React.useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false);
    const [selectedChat, setSelectedChat] = React.useState<{
    id: string;
    title: string;
  } | null>(null);
  const [newChatTitle, setNewChatTitle] = React.useState("");
  // Use isCreatingChat from context to prevent duplicate chat creation

  const handleRenameChat = async () => {
    if (!selectedChat || !newChatTitle.trim()) return;
    console.log(
      "[MainLayout] handleRenameChat:",
      selectedChat.id,
      "→",
      newChatTitle
    );
    try {
      await api.chats.rename(selectedChat.id, { title: newChatTitle });
      console.log("[MainLayout] handleRenameChat: Renamed successfully");

      // Force refresh to show new title immediately
      await refreshChats(true);
      console.log("[MainLayout] handleRenameChat: Chat list refreshed");

      // If this is the current conversation, update it too
      if (currentConversation?.id === selectedChat.id) {
        await selectConversation(selectedChat.id);
        console.log(
          "[MainLayout] handleRenameChat: Updated current conversation"
        );
      }

      // Close dialog
      setRenameDialogOpen(false);
      setSelectedChat(null);
      setNewChatTitle("");
    } catch (error) {
      console.error("[MainLayout] handleRenameChat: Failed", error);
    }
  };

  const handleDeleteChat = async () => {
    if (!selectedChat) return;
    console.log("[MainLayout] handleDeleteChat:", selectedChat.id);

    const wasCurrentChat = currentConversation?.id === selectedChat.id;
    const deletedChatId = selectedChat.id;

    // Close dialog immediately for better UX
    setDeleteDialogOpen(false);
    setSelectedChat(null);

    try {
      // Delete the chat
      await api.chats.delete(deletedChatId);
      console.log("[MainLayout] handleDeleteChat: Deleted chat successfully");
    } catch (error: any) {
      // If 404 (not found), treat as already deleted - still proceed with cleanup
      const isNotFound = error?.message?.includes("404") || error?.message?.includes("not found");
      if (!isNotFound) {
        console.error("[MainLayout] handleDeleteChat: Failed", error);
        return;
      }
      console.log("[MainLayout] handleDeleteChat: Chat already deleted, cleaning up UI");
    }

    // Force refresh to remove deleted chat immediately
    await refreshChats(true);
    console.log("[MainLayout] handleDeleteChat: Chat list refreshed");

    // If deleted chat was the current one, auto-select next
    if (wasCurrentChat) {
      setTimeout(async () => {
        const updatedChats = await api.chats.list();
        const sortedChats = (updatedChats.conversations || []).sort(
          (a, b) => {
            const dateA = a.updated_at ? new Date(a.updated_at).getTime() : 0;
            const dateB = b.updated_at ? new Date(b.updated_at).getTime() : 0;
            return dateB - dateA;
          }
        );

        console.log(
          "[MainLayout] handleDeleteChat: Available chats after delete:",
          sortedChats.length
        );

        if (sortedChats.length > 0) {
          const nextChat = sortedChats[0];
          console.log(
            "[MainLayout] handleDeleteChat: Auto-selecting next chat:",
            nextChat.id,
            nextChat.title
          );
          await selectConversation(nextChat.id);
          navigate(`/chat/${nextChat.id}`);
        } else {
          console.log(
            "[MainLayout] handleDeleteChat: No chats remaining, navigating to /chat"
          );
          navigate("/chat");
        }
      }, 100);
    }
  };

  const handleMoveToProject = async (
    chatId: string,
    projectId: string | null
  ) => {
    console.log("[MainLayout] handleMoveToProject:", chatId, "→", projectId);
    try {
      // assignChatToProject already force-refreshes chats and projects
      await assignChatToProject(chatId, projectId);
      console.log("[MainLayout] handleMoveToProject: Moved successfully");
    } catch (error) {
      console.error("[MainLayout] handleMoveToProject: Failed", error);
    }
  };

  const handleNewChat = async () => {
    console.log("[MainLayout] handleNewChat called, isCreatingChat:", isCreatingChat);
    
    // Don't create if already creating
    if (isCreatingChat) {
      console.log("[MainLayout] Already creating chat, skipping");
      return;
    }
    
    try {
      const newConversation = await createConversation();
      console.log("[MainLayout] Created conversation:", newConversation?.id);
      if (newConversation?.id) {
        // Navigate to the new chat
        navigate(`/chat/${newConversation.id}`);
      }
    } catch (error: any) {
      // Log all errors for debugging
      console.error("[MainLayout] handleNewChat error:", error?.message || error);
      // Show user-friendly message if backend is down
      if (error?.message?.includes("fetch") || error?.message?.includes("network")) {
        alert("Cannot connect to server. Please make sure the backend is running.");
      }
    }
  };

  const isActive = (pageName) => {
    if (pageName === "Admin") {
      return location.pathname === "/admin";
    }
    return location.pathname === createPageUrl(pageName);
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-950 via-black to-gray-950 text-gray-100 overflow-hidden">
      {/* Sidebar */}
      <div
        className={`bg-gradient-to-b from-gray-950 to-black border-r border-gray-800/30 flex flex-col transition-all duration-300 ${
          sidebarCollapsed ? "w-20" : "w-72"
        }`}
      >
        {/* Logo & Brand */}
        <div className="p-6 border-b border-gray-800/50 relative">
          {!sidebarCollapsed ? (
            <>
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 via-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                  <Sparkles className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-lg font-semibold text-white">Avalon</h1>
                  <p className="text-xs text-gray-500">Research Intelligence</p>
                </div>
              </div>

              {/* Close Button */}
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebarCollapsed(true)}
                className="absolute top-4 right-4 text-gray-400 hover:text-gray-200 hover:bg-gray-800/50 w-8 h-8"
              >
                <X className="w-4 h-4" />
              </Button>

              {/* New Chat Button */}
              <Button
                onClick={handleNewChat}
                disabled={isCreatingChat}
                className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white shadow-lg shadow-blue-500/30 transition-all duration-300 hover:shadow-blue-500/50 hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isCreatingChat ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Plus className="w-4 h-4 mr-2" />
                )}
                New Chat
              </Button>

              </>
          ) : (
            <div className="flex flex-col items-center gap-4">
              {/* Logo with Hamburger on Hover */}
              <div
                className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 via-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20 cursor-pointer transition-all duration-300 hover:shadow-blue-500/40"
                onMouseEnter={() => setLogoHovered(true)}
                onMouseLeave={() => setLogoHovered(false)}
                onClick={() => setSidebarCollapsed(false)}
              >
                {logoHovered ? (
                  <Menu className="w-6 h-6 text-white" />
                ) : (
                  <Sparkles className="w-6 h-6 text-white" />
                )}
              </div>

              {/* New Chat Icon */}
              <Button
                size="icon"
                onClick={handleNewChat}
                disabled={isCreatingChat}
                className="w-10 h-10 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50 hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                title="New Chat"
              >
                {isCreatingChat ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Plus className="w-4 h-4" />
                )}
              </Button>

              </div>
          )}
        </div>

        {/* Navigation */}
        <ScrollArea className="flex-1 px-3 py-4">
          {!sidebarCollapsed ? (
            <>
              <div className="space-y-2 mb-4">
                <Button
                  variant="ghost"
                  onClick={() => setSearchModalOpen(true)}
                  className="w-full justify-start text-gray-400 hover:text-gray-200 hover:bg-gray-800/50 transition-all duration-200"
                >
                  <Search className="w-4 h-4 mr-3" />
                  Search Chats
                </Button>

                <Link key="reports-link" to={createPageUrl("Reports")}>
                  <Button
                    variant="ghost"
                    className={`w-full justify-start transition-all duration-200 ${
                      isActive("Reports")
                        ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-lg shadow-cyan-500/10"
                        : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/50"
                    }`}
                  >
                    <FileText className="w-4 h-4 mr-3" />
                    Reports Library
                  </Button>
                </Link>
              </div>

              {/* Projects Section */}
              <Collapsible open={projectsOpen} onOpenChange={setProjectsOpen}>
                <CollapsibleTrigger className="flex items-center justify-between w-full px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider hover:text-gray-300 transition-colors">
                  <span>Projects</span>
                  <ChevronRight
                    className={`w-4 h-4 transition-transform duration-200 ${
                      projectsOpen ? "rotate-90" : ""
                    }`}
                  />
                </CollapsibleTrigger>
                <CollapsibleContent className="space-y-1 mt-2">
                  <Link to={createPageUrl("Projects")}>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="w-full justify-start text-gray-400 hover:text-cyan-400 hover:bg-cyan-500/5 border border-dashed border-gray-700 hover:border-cyan-500/30 transition-all"
                    >
                      <Plus className="w-3 h-3 mr-2" />
                      Create New Project
                    </Button>
                  </Link>
                  {projects.map((project) => (
                    <Link key={project.id} to={createPageUrl("Projects")}>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="w-full justify-start text-gray-400 hover:text-gray-200 hover:bg-gray-800/50 group"
                      >
                        <FolderOpen className="w-3 h-3 mr-2 text-green-500 group-hover:text-green-400" />
                        <span className="flex-1 text-left truncate text-xs">
                          {project.name}
                        </span>
                        <span className="text-xs text-gray-600">
                          {project.chat_ids?.length ?? 0}
                        </span>
                      </Button>
                    </Link>
                  ))}
                </CollapsibleContent>
              </Collapsible>

              {/* Past Chats */}
              <div className="mt-6">
                <Collapsible open={chatsOpen} onOpenChange={setChatsOpen}>
                  <CollapsibleTrigger className="flex items-center justify-between w-full px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider hover:text-gray-300 transition-colors">
                    <span>Recent Chats</span>
                    <ChevronRight
                      className={`w-4 h-4 transition-transform duration-200 ${
                        chatsOpen ? "rotate-90" : ""
                      }`}
                    />
                  </CollapsibleTrigger>
                  <CollapsibleContent className="space-y-1 mt-2">
                    {chats.filter((chat) => chat?.id).length === 0 && (
                      <div className="text-xs text-gray-500 px-3 py-2 italic">
                        No recent chats. Click "New Chat" to start.
                      </div>
                    )}
                    {chats
                      .filter((chat) => chat?.id)
                      .map((chat) => (
                        <div
                          key={chat.id}
                          className={`group relative flex items-center w-full rounded-md hover:bg-gray-800/50 transition-all ${
                            currentConversation?.id === chat.id
                              ? "bg-gray-800/60"
                              : ""
                          }`}
                        >
                          <div
                            onClick={async (e) => {
                              e.stopPropagation();
                              console.log(
                                "[MainLayout] Chat clicked:",
                                chat.id,
                                chat.title
                              );

                              // Skip if already selected
                              if (currentConversation?.id === chat.id) {
                                console.log(
                                  "[MainLayout] Chat already selected, skipping"
                                );
                                return;
                              }

                              try {
                                await selectConversation(chat.id);
                                navigate(`/chat/${chat.id}`);
                                console.log(
                                  "[MainLayout] Navigated to chat:",
                                  chat.id
                                );
                              } catch (error) {
                                console.error(
                                  "[MainLayout] Failed to select chat:",
                                  error
                                );
                              }
                            }}
                            className="flex-1 flex items-center justify-start text-gray-400 hover:text-gray-200 p-2 cursor-pointer"
                          >
                            <History className="w-3 h-3 mr-2 text-blue-500/50 group-hover:text-blue-400 flex-shrink-0" />
                            <div className="flex-1 text-left min-w-0">
                              <div className="text-xs truncate">
                                {chat.title}
                              </div>
                              <div className="text-xs text-gray-600">
                                {chat.updated_at
                                  ? new Date(chat.updated_at).toLocaleString()
                                  : ""}
                              </div>
                            </div>
                          </div>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6 mr-1 text-gray-500 opacity-0 group-hover:opacity-100 hover:text-gray-300 hover:bg-gray-700/50 transition-all"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  console.log(
                                    "[MainLayout] Three-dots menu clicked for chat:",
                                    chat.id
                                  );
                                }}
                              >
                                <MoreVertical className="w-4 h-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent
                              align="end"
                              onClick={(e) => e.stopPropagation()}
                              className="bg-gray-900 border-gray-700 min-w-[180px]"
                            >
                              {/* Rename */}
                              <DropdownMenuItem
                                onClick={() => {
                                  if (!chat.id) return;
                                  setSelectedChat({
                                    id: chat.id,
                                    title: chat.title,
                                  });
                                  setNewChatTitle(chat.title);
                                  setRenameDialogOpen(true);
                                }}
                                className="text-gray-200 hover:bg-gray-800"
                              >
                                <Edit3 className="w-4 h-4 mr-2 text-blue-400" />
                                <span>Rename</span>
                              </DropdownMenuItem>

                              {/* Move to Project */}
                              <DropdownMenuSub>
                                <DropdownMenuSubTrigger className="text-gray-200 hover:bg-gray-800">
                                  <FolderPlus className="w-4 h-4 mr-2 text-green-400" />
                                  <span>Move to Project</span>
                                </DropdownMenuSubTrigger>
                                <DropdownMenuSubContent className="bg-gray-900 border-gray-700">
                                  <DropdownMenuItem
                                    onClick={() => {
                                      if (!chat.id) return;
                                      handleMoveToProject(chat.id, null);
                                    }}
                                    className="text-gray-200 hover:bg-gray-800"
                                  >
                                    {chat.project_id === null ? (
                                      <Check className="w-4 h-4 mr-2 text-green-400" />
                                    ) : (
                                      <span className="w-4 h-4 mr-2" />
                                    )}
                                    <span>No Project</span>
                                  </DropdownMenuItem>
                                  {projects.map((project) => (
                                    <DropdownMenuItem
                                      key={project.id}
                                      onClick={() => {
                                        if (!chat.id) return;
                                        handleMoveToProject(chat.id, project.id);
                                      }}
                                      className="text-gray-200 hover:bg-gray-800"
                                    >
                                      {chat.project_id === project.id ? (
                                        <Check className="w-4 h-4 mr-2 text-green-400" />
                                      ) : (
                                        <span className="w-4 h-4 mr-2" />
                                      )}
                                      <span>{project.name}</span>
                                    </DropdownMenuItem>
                                  ))}
                                </DropdownMenuSubContent>
                              </DropdownMenuSub>

                              <DropdownMenuSeparator className="bg-gray-800" />

                              {/* Start Group Chat */}
                              <DropdownMenuItem
                                onClick={(e) => {
                                  e.stopPropagation();
                                  if (!chat.id) return;
                                  setModalState({
                                    groupChat: { chatId: chat.id },
                                  });
                                }}
                                className="text-gray-200 hover:bg-gray-800"
                              >
                                <Users className="w-4 h-4 mr-2 text-cyan-400" />
                                <span>Start a Group Chat</span>
                              </DropdownMenuItem>

                              <DropdownMenuSeparator className="bg-gray-800" />

                              {/* Delete */}
                              <DropdownMenuItem
                                onClick={() => {
                                  if (!chat.id) return;
                                  setSelectedChat({
                                    id: chat.id,
                                    title: chat.title,
                                  });
                                  setDeleteDialogOpen(true);
                                }}
                                className="text-red-400 hover:text-red-300 hover:bg-gray-800"
                              >
                                <Trash2 className="w-4 h-4 mr-2" />
                                <span>Delete</span>
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      ))}
                  </CollapsibleContent>
                </Collapsible>
              </div>
            </>
          ) : (
            // Collapsed sidebar - only icons
            <div className="flex flex-col items-center gap-3">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSearchModalOpen(true)}
                className="w-10 h-10 text-gray-400 hover:text-gray-200 hover:bg-gray-800/50 transition-all duration-200"
                title="Search Chats"
              >
                <Search className="w-5 h-5" />
              </Button>

              <Link key="reports-link-collapsed" to={createPageUrl("Reports")}>
                <Button
                  variant="ghost"
                  size="icon"
                  className={`w-10 h-10 transition-all duration-200 ${
                    isActive("Reports")
                      ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30"
                      : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/50"
                  }`}
                  title="Reports Library"
                >
                  <FileText className="w-5 h-5" />
                </Button>
              </Link>

              <Link
                key="projects-link-collapsed"
                to={createPageUrl("Projects")}
              >
                <Button
                  variant="ghost"
                  size="icon"
                  className={`w-10 h-10 transition-all duration-200 ${
                    isActive("Projects")
                      ? "bg-green-500/10 text-green-400 border border-green-500/30"
                      : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/50"
                  }`}
                  title="Projects"
                >
                  <FolderOpen className="w-5 h-5" />
                </Button>
              </Link>
            </div>
          )}
        </ScrollArea>

        {/* Settings & Admin at Bottom */}
        <div className="p-3 border-t border-gray-800/50 space-y-2">
          {!sidebarCollapsed ? (
            <React.Fragment>
              <Link to="/admin" key="admin-link">
                <Button
                  variant="ghost"
                  className={`w-full justify-start transition-all duration-200 ${
                    isActive("Admin")
                      ? "bg-purple-500/10 text-purple-400 border border-purple-500/30"
                      : "text-gray-400 hover:text-purple-400 hover:bg-purple-500/10"
                  }`}
                >
                  <Shield className="w-4 h-4 mr-3" />
                  Admin
                </Button>
              </Link>
              <Link to={createPageUrl("Settings")} key="settings-link">
                <Button
                  variant="ghost"
                  className={`w-full justify-start transition-all duration-200 ${
                    isActive("Settings")
                      ? "bg-gray-800 text-gray-200"
                      : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/50"
                  }`}
                >
                  <Settings className="w-4 h-4 mr-3" />
                  Settings
                </Button>
              </Link>
            </React.Fragment>
          ) : (
            <React.Fragment>
              <Link to="/admin" key="admin-link-collapsed">
                <Button
                  variant="ghost"
                  size="icon"
                  className={`w-10 h-10 transition-all duration-200 ${
                    isActive("Admin")
                      ? "bg-purple-500/10 text-purple-400 border border-purple-500/30"
                      : "text-gray-400 hover:text-purple-400 hover:bg-purple-500/10"
                  }`}
                  title="Admin Dashboard"
                >
                  <Shield className="w-5 h-5" />
                </Button>
              </Link>
              <Link
                to={createPageUrl("Settings")}
                key="settings-link-collapsed"
              >
                <Button
                  variant="ghost"
                  size="icon"
                  className={`w-10 h-10 transition-all duration-200 ${
                    isActive("Settings")
                      ? "bg-gray-800 text-gray-200"
                      : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/50"
                  }`}
                  title="Settings"
                >
                  <Settings className="w-5 h-5" />
                </Button>
              </Link>
            </React.Fragment>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden bg-gradient-to-br from-gray-950 via-black to-gray-950">
        {children}
      </div>

      {/* Search Chats Modal */}
      <SearchChatsModal
        isOpen={searchModalOpen}
        onClose={() => setSearchModalOpen(false)}
      />

      {/* Rename Chat Dialog */}
      <Dialog open={renameDialogOpen} onOpenChange={setRenameDialogOpen}>
        <DialogContent className="bg-gray-900 border-gray-800 text-gray-200">
          <DialogHeader>
            <DialogTitle className="text-xl font-semibold text-white">
              Rename Chat
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label htmlFor="chat-title" className="text-gray-300">
                Chat Title
              </Label>
              <Input
                id="chat-title"
                value={newChatTitle}
                onChange={(e) => setNewChatTitle(e.target.value)}
                placeholder="Enter chat title"
                className="bg-black border-gray-800 text-gray-300"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    handleRenameChat();
                  }
                }}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button
                variant="ghost"
                onClick={() => {
                  setRenameDialogOpen(false);
                  setSelectedChat(null);
                  setNewChatTitle("");
                }}
                className="text-gray-400 hover:text-gray-200"
              >
                Cancel
              </Button>
              <Button
                onClick={handleRenameChat}
                className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500"
                disabled={!newChatTitle.trim()}
              >
                Save
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Chat Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent className="bg-gray-900 border-gray-800 text-gray-200">
          <DialogHeader>
            <DialogTitle className="text-xl font-semibold text-white">
              Delete Chat
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <p className="text-gray-400">
              Are you sure you want to delete "{selectedChat?.title}"? This
              action cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <Button
                variant="ghost"
                onClick={() => {
                  setDeleteDialogOpen(false);
                  setSelectedChat(null);
                }}
                className="text-gray-400 hover:text-gray-200"
              >
                Cancel
              </Button>
              <Button
                onClick={handleDeleteChat}
                className="bg-red-600 hover:bg-red-500 text-white"
              >
                Delete
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Group Chat Modal */}
      <GroupChatModal
        isOpen={!!modals.groupChat}
        onClose={() => setModalState({ groupChat: null })}
        chatId={modals.groupChat?.chatId || null}
      />
    </div>
  );
}
