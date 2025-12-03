import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  api,
  ChatSummary,
  Conversation,
  Project,
  Report,
  SettingsPayload,
} from "@/lib/api";
import { useNavigate } from "react-router-dom";

type ModalState = {
  pdf?: { reportId: string; fileUrl?: string; title?: string } | null;
  csv?: { reportId: string; fileUrl?: string; title?: string } | null;
  graph?: { graphId: string } | null;
  groupChat?: { chatId: string } | null;
};

type UploadDescriptor = {
  id: string;
  name: string;
  size?: number;
};

type AppContextValue = {
  chats: ChatSummary[];
  currentConversation: Conversation | null;
  projects: Project[];
  reports: Report[];
  uploads: UploadDescriptor[];
  settings: SettingsPayload | null;
  modals: ModalState;
  loading: boolean;
  error: string | null;
  // Thinking state
  isThinking: boolean;
  setIsThinking: (value: boolean) => void;
  // Streaming state
  isStreaming: boolean;
  setIsStreaming: (value: boolean) => void;
  // Mock research insights toggle (UI only)
  useMockResearchInsights: boolean;
  setUseMockResearchInsights: (value: boolean) => void;
  // Chat creation state
  isCreatingChat: boolean;
  // Agent timeline state
  agentTimeline: Record<
    string,
    { status: "pending" | "running" | "completed"; message?: string }
  >;
  setAgentTimeline: (
    timeline: Record<
      string,
      { status: "pending" | "running" | "completed"; message?: string }
    >
  ) => void;
  updateAgentTimeline: (
    agentName: string,
    status: "pending" | "running" | "completed",
    message?: string
  ) => void;
  resetAgentTimeline: () => void;
  refreshAll: () => Promise<void>;
  refreshChats: (force?: boolean) => Promise<void>;
  selectConversation: (id: string | null) => Promise<void>;
  createConversation: (payload?: {
    title?: string;
    project_id?: string | null;
  }) => Promise<Conversation>;
  addUpload: (file: UploadDescriptor) => void;
  removeUpload: (id: string) => void;
  setModalState: (modal: Partial<ModalState>) => void;
  updateSettings: (payload: SettingsPayload) => Promise<void>;
  assignChatToProject: (
    chatId: string,
    projectId: string | null
  ) => Promise<void>;
  refreshProjects: (force?: boolean) => Promise<void>;
};

const AppContext = createContext<AppContextValue | undefined>(undefined);

export const AppProvider = ({ children }: { children: React.ReactNode }) => {
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [currentConversation, setCurrentConversation] =
    useState<Conversation | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [uploads, setUploads] = useState<UploadDescriptor[]>([]);
  const [settings, setSettings] = useState<SettingsPayload | null>(null);
  const [modals, setModals] = useState<ModalState>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chatsLastFetched, setChatsLastFetched] = useState<number>(0);
  const [isCreatingChat, setIsCreatingChat] = useState(false);

  // Thinking state
  const [isThinking, setIsThinking] = useState(false);
  // Streaming state
  const [isStreaming, setIsStreaming] = useState(false);
  // Mock research insights toggle (UI only - for prototyping)
  const [useMockResearchInsights, setUseMockResearchInsights] = useState(true);
  // Agent timeline state
  const [agentTimeline, setAgentTimeline] = useState<
    Record<
      string,
      { status: "pending" | "running" | "completed"; message?: string }
    >
  >({});

  const updateAgentTimeline = useCallback(
    (
      agentName: string,
      status: "pending" | "running" | "completed",
      message?: string
    ) => {
      setAgentTimeline((prev) => ({
        ...prev,
        [agentName]: { status, message },
      }));
    },
    []
  );

  const resetAgentTimeline = useCallback(() => {
    setAgentTimeline({});
  }, []);

  const fetchChats = useCallback(
    async (force: boolean = false) => {
      // Client-side caching - only refetch if forced or >5 seconds old
      const now = Date.now();
      if (!force && chatsLastFetched && now - chatsLastFetched < 5000) {
        console.log("[AppContext] fetchChats: Using cached data");
        return;
      }

      console.log("[AppContext] fetchChats: Fetching from server...");
      const response = await api.chats.list();
      const sortedChats = (response.conversations || []).sort((a, b) => {
        const dateA = a.updated_at ? new Date(a.updated_at).getTime() : 0;
        const dateB = b.updated_at ? new Date(b.updated_at).getTime() : 0;
        return dateB - dateA;
      });
      console.log(
        "[AppContext] fetchChats: Fetched",
        sortedChats.length,
        "chats"
      );
      setChats(sortedChats);
      setChatsLastFetched(now);
    },
    [chatsLastFetched]
  );

  const fetchProjects = useCallback(async (force: boolean = false) => {
    // Projects change less frequently, cache not needed yet
    const response = await api.projects.list();
    setProjects(response.projects || []);
  }, []);

  const fetchReports = useCallback(async () => {
    const response = await api.reports.list();
    setReports(response.reports || []);
  }, []);

  const fetchSettings = useCallback(async () => {
    const response = await api.settings.get();
    setSettings(response);
  }, []);

  const refreshAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await Promise.all([
        fetchChats(),
        fetchProjects(),
        fetchReports(),
        fetchSettings(),
      ]);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [fetchChats, fetchProjects, fetchReports, fetchSettings]);

  // Initialize app data on mount
  useEffect(() => {
    const initializeApp = async () => {
      try {
        await refreshAll().catch((err) => {
          console.error(
            "[AppContext] Error refreshing data on initial load:",
            err
          );
          // Don't block the app if refresh fails
        });
      } catch (err) {
        console.error("[AppContext] Fatal error during initialization:", err);
      }
    };

    initializeApp();
  }, [refreshAll]);

  const selectConversation = useCallback(
    async (id: string | null) => {
      console.log("[AppContext] selectConversation:", id);
      if (!id) {
        setCurrentConversation(null);
        return;
      }
      try {
        setLoading(true);
        const conversation = await api.chats.get(id);
        console.log(
          "[AppContext] selectConversation: Loaded conversation",
          conversation.title
        );
        setCurrentConversation(conversation);

        // Use cached chats (backend updates timestamps automatically)
        await fetchChats(false);
        console.log("[AppContext] selectConversation: Using cached chat list");
      } catch (err) {
        console.error("[AppContext] selectConversation: Error", err);
        setError((err as Error).message);
        throw err; // Re-throw so caller knows it failed
      } finally {
        setLoading(false);
      }
    },
    [fetchChats]
  );

  const createConversation = useCallback(
    async (payload?: {
      title?: string;
      project_id?: string | null;
    }): Promise<Conversation> => {
      // Prevent duplicate creation
      if (isCreatingChat) {
        console.log("[AppContext] createConversation: Already in progress");
        throw new Error("Already creating chat");
      }

      setIsCreatingChat(true);
      setError(null);
      
      try {
        // Generate default title if not provided
        const title = payload?.title || `New Chat`;
        console.log("[AppContext] Creating new chat with title:", title);
        
        const response = await api.chats.create({ ...payload, title });
        
        if (!response?.conversation_id) {
          throw new Error("Failed to create conversation - no ID returned");
        }
        
        console.log("[AppContext] Created chat:", response.conversation_id);

        // Fetch the complete conversation object
        const newConversation = await api.chats.get(response.conversation_id);
        console.log("[AppContext] Fetched new conversation:", newConversation);
        
        // Set as current conversation immediately
        setCurrentConversation(newConversation);

        // Force refresh chats list to show new chat in Recent Chats
        setChatsLastFetched(0); // Reset cache
        await fetchChats(true);
        console.log("[AppContext] Chats list refreshed");

        return newConversation;
      } catch (err: any) {
        console.error("[AppContext] createConversation error:", err);
        const errorMessage = err?.message || "Failed to create conversation";
        setError(errorMessage);
        throw err;
      } finally {
        setIsCreatingChat(false);
      }
    },
    [isCreatingChat, fetchChats]
  );

  const addUpload = useCallback((file: UploadDescriptor) => {
    setUploads((prev) => [...prev, file]);
  }, []);

  const removeUpload = useCallback((id: string) => {
    setUploads((prev) => prev.filter((file) => file.id !== id));
  }, []);

  const setModalState = useCallback((updates: Partial<ModalState>) => {
    setModals((prev) => ({ ...prev, ...updates }));
  }, []);

  const updateSettings = useCallback(async (payload: SettingsPayload) => {
    await api.settings.update(payload);
    setSettings(payload);
  }, []);

  const assignChatToProject = useCallback(
    async (chatId: string, projectId: string | null) => {
      if (!chatId) return;
      try {
        setLoading(true);
        // Get current conversation to check if it has a project
        const currentChat = chats.find((c) => c.id === chatId);
        const oldProjectId = currentChat?.project_id;

        if (projectId) {
          // If moving to a new project, remove from old project first
          if (oldProjectId && oldProjectId !== projectId) {
            try {
              await api.projects.removeChat(oldProjectId, { chat_id: chatId });
            } catch (err) {
              // Ignore errors if chat wasn't in the old project
              console.warn("Error removing chat from old project:", err);
            }
          }
          // Add to new project (this also updates the conversation's project_id)
          await api.projects.addChat(projectId, { chat_id: chatId });
        } else {
          // Removing from project
          if (oldProjectId) {
            // Remove from project's chat_ids
            await api.projects.removeChat(oldProjectId, { chat_id: chatId });
          }
          // Also update conversation's project_id to null
          await api.chats.assignProject(chatId, { project_id: null });
        }

        // Force refresh chats to show updated project assignment
        await fetchChats(true);

        // Force refresh projects to update chat counts
        await fetchProjects(true);

        // Refresh current conversation if it's the one being updated
        if (currentConversation?.id === chatId) {
          await selectConversation(chatId);
        }
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    },
    [fetchChats, fetchProjects, chats, currentConversation, selectConversation]
  );

  // Memoize actions separately - these rarely change
  const actions = useMemo(
    () => ({
      refreshAll,
      refreshChats: fetchChats,
      refreshProjects: fetchProjects,
      selectConversation,
      createConversation,
      addUpload,
      removeUpload,
      setModalState,
      updateSettings,
      assignChatToProject,
      setIsThinking,
      setIsStreaming,
      setAgentTimeline,
      updateAgentTimeline,
      resetAgentTimeline,
    }),
    [
      refreshAll,
      fetchChats,
      fetchProjects,
      selectConversation,
      createConversation,
      addUpload,
      removeUpload,
      setModalState,
      updateSettings,
      assignChatToProject,
      updateAgentTimeline,
      resetAgentTimeline,
    ]
  );

  // Combine everything into context value
  const value = useMemo<AppContextValue>(
    () => ({
      chats,
      currentConversation,
      projects,
      reports,
      uploads,
      settings,
      modals,
      loading,
      error,
      isThinking,
      isStreaming,
      useMockResearchInsights,
      setUseMockResearchInsights,
      isCreatingChat,
      agentTimeline,
      ...actions,
    }),
    [
      chats,
      currentConversation,
      projects,
      reports,
      uploads,
      settings,
      modals,
      loading,
      error,
      isThinking,
      isStreaming,
      useMockResearchInsights,
      isCreatingChat,
      agentTimeline,
      actions,
    ]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useAppContext must be used within AppProvider");
  }
  return context;
};
