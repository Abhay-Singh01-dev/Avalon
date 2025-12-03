import React, { useState, useRef, useEffect, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Sparkles, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import TopBar from "@/components/chat/TopBar";
import MessageBubble from "@/components/chat/MessageBubble";
import StreamingMessageBubble from "@/components/chat/StreamingMessageBubble";
import ChatInput from "@/components/chat/ChatInput";
import MultiAgentRenderer from "@/components/chat/agents/MultiAgentRenderer";
import ThinkingIndicator from "@/components/chat/ThinkingIndicator";
import ThinkingPanel from "@/components/chat/ThinkingPanel";
import AgentTimeline from "@/components/chat/AgentTimeline";
import { ResearchInsightsTable } from "@/components/insights/ResearchInsightsTable";
import { useAppContext } from "@/context/AppContext";
import { api } from "@/lib/api";

export default function ChatPage() {
  const { id: chatIdFromUrl } = useParams<{ id?: string }>();
  const navigate = useNavigate();
  const {
    currentConversation,
    selectConversation,
    createConversation,
    uploads,
    loading: contextLoading,
    isThinking,
    setIsThinking,
    isStreaming,
    setIsStreaming,
    agentTimeline,
    updateAgentTimeline,
    resetAgentTimeline,
    refreshChats,
  } = useAppContext();
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState<string>("");
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(
    null
  );
  const [completedMessages, setCompletedMessages] = useState<
    Array<{ id: string; text: string; isUser: boolean; metadata?: any }>
  >([]);
  const [timelineCollapsed, setTimelineCollapsed] = useState(false);
  const [showReportButton, setShowReportButton] = useState(false);
  const [reportData, setReportData] = useState<Record<string, any> | null>(
    null
  );
  // Data Source RAG indicator
  const [dataSourceIndicator, setDataSourceIndicator] = useState<string | null>(null);
  
  // Thinking Panel state - PHI detection and routing messages
  const [showThinkingPanel, setShowThinkingPanel] = useState(false);
  const [routingMessage, setRoutingMessage] = useState<string>("");
  const [modeMessage, setModeMessage] = useState<string>("");
  
  const scrollRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const isCreatingConversationRef = useRef<boolean>(false);

  // Convert conversation messages to UI format and merge with completed messages
  const messages = useMemo(() => {
    const conversationMsgs = currentConversation?.messages
      ? currentConversation.messages.map((msg) => ({
          id: msg.id,
          text: msg.content,
          isUser: msg.role === "user",
          metadata: msg.metadata,
        }))
      : [];

    // Merge conversation messages with locally completed messages
    return [...conversationMsgs, ...completedMessages];
  }, [currentConversation, completedMessages]);

  // Throttled scroll to prevent jiggling
  const scrollTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const scrollToBottom = (immediate = false) => {
    if (scrollRef.current) {
      if (immediate) {
        scrollRef.current.scrollIntoView({ behavior: "auto", block: "end" });
      } else {
        // Throttle scroll updates during streaming
        if (scrollTimeoutRef.current) {
          clearTimeout(scrollTimeoutRef.current);
        }
        scrollTimeoutRef.current = setTimeout(() => {
          if (scrollRef.current) {
            scrollRef.current.scrollIntoView({
              behavior: "auto",
              block: "end",
            });
          }
        }, 100); // Update scroll every 100ms max
      }
    }
  };

  useEffect(() => {
    scrollToBottom(true); // Immediate scroll for new messages
  }, [messages]);

  // Throttled scroll during streaming only
  useEffect(() => {
    if (streamingMessage) {
      scrollToBottom(false); // Throttled scroll during streaming
    }
  }, [streamingMessage]);

  // Sync conversation with URL parameter
  useEffect(() => {
    // Skip if context is still loading initial data
    if (contextLoading) {
      return;
    }

    // If URL has a valid chat ID, load that conversation
    if (chatIdFromUrl && chatIdFromUrl !== "undefined" && chatIdFromUrl !== "null") {
      // Only select if different from current
      if (currentConversation?.id !== chatIdFromUrl) {
        console.log("[ChatPage] Loading conversation from URL:", chatIdFromUrl);
        selectConversation(chatIdFromUrl).catch((err) => {
          console.error("[ChatPage] Failed to load conversation:", err);
          // If conversation not found, redirect to /chat to create new one
          navigate("/chat", { replace: true });
        });
      }
    }
    // Note: We don't auto-create a chat here anymore - MainLayout handles New Chat button
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chatIdFromUrl, contextLoading]);

  // Reset completed messages when conversation changes
  useEffect(() => {
    setCompletedMessages([]);
  }, [currentConversation?.id]);

  const [pendingUserMessage, setPendingUserMessage] = useState<string | null>(
    null
  );
  const [pendingUserFiles, setPendingUserFiles] = useState<Array<{id: string; name: string; size?: number}>>([]);

  const handleSendMessage = async (userMessage: string) => {
    let conversationId = currentConversation?.id;

    // STEP 1: Display user message IMMEDIATELY in UI with files
    setPendingUserMessage(userMessage);
    // Store the files to display with the pending message
    const currentFiles = uploads.map(f => ({ id: f.id, name: f.name, size: f.size }));
    setPendingUserFiles(currentFiles);

    // Create conversation if none exists
    if (!conversationId) {
      try {
        const response = await api.chats.create({});
        conversationId = response.conversation_id;
        await selectConversation(response.conversation_id);
      } catch (error) {
        console.error("Failed to create conversation:", error);
        setPendingUserMessage(null); // Clear on error
        setPendingUserFiles([]);
        return;
      }
    }

    // Ensure we have a conversation ID before proceeding
    if (!conversationId) {
      console.error("No conversation ID available");
      setPendingUserMessage(null); // Clear on error
      setPendingUserFiles([]);
      return;
    }

    // Cancel any existing stream
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // STEP 2: Start streaming state
    setIsLoading(true);
    setIsThinking(true);
    setIsStreaming(true);
    setStreamingMessage("");
    setStreamingMessageId(null);
    setDataSourceIndicator(null);  // Clear data source indicator
    resetAgentTimeline();
    
    // Reset thinking panel state
    setShowThinkingPanel(false);
    setRoutingMessage("");
    setModeMessage("");

    try {
      // Collect file IDs from uploaded files
      const fileIds = uploads.map((file) => file.id).filter(Boolean);

      // Use streaming API
      let firstTokenReceived = false;
      let fullContent = "";

      for await (const chunk of api.chats.askStream(
        {
          conversation_id: conversationId,
          message: userMessage,
          attachments: fileIds.length > 0 ? fileIds : undefined,
        },
        abortController.signal
      )) {
        if (chunk.error) {
          console.error("Streaming error:", chunk.error);
          break;
        }

        // Handle report generation signal
        if (chunk.report_ready) {
          console.log(
            "[REPORT_READY] Report generation signal received",
            chunk.report_data
          );
          setShowReportButton(true);
          setReportData(chunk.report_data || null);
          continue;
        }

        // Handle Data Source RAG indicator
        if (chunk.type === "data_source_used") {
          console.log("[DATA_SOURCE_RAG] Using data sources:", chunk.indicator);
          setDataSourceIndicator(chunk.indicator);
          continue;
        }

        // Handle THINKING event - PHI detection routing message (FIRST event)
        if (chunk.type === "thinking") {
          console.log("[THINKING_PANEL] Received:", chunk.message);
          setRoutingMessage(chunk.message);
          setShowThinkingPanel(true);
          continue;
        }

        // Handle ROUTING event - contains mode information
        if (chunk.type === "routing") {
          console.log("[ROUTING] Mode:", chunk.detected_mode, "Reason:", chunk.mode_reason);
          // Update mode message for thinking panel
          if (chunk.detected_mode && chunk.mode_reason) {
            setModeMessage(`${chunk.detected_mode} - ${chunk.mode_reason}`);
          }
          continue;
        }

        // Handle timeline events
        if (chunk.type === "timeline" || chunk.event) {
          const event = chunk.event || chunk.type;
          const agent = chunk.agent || "unknown";

          if (event === "agent_start") {
            // Check if message indicates "queued" vs "starting"
            if (chunk.message && chunk.message.includes("queued")) {
              updateAgentTimeline(agent, "pending", chunk.message);
            } else {
              updateAgentTimeline(agent, "running", chunk.message);
            }
          } else if (
            event === "decomposition_start" ||
            event === "synthesis_start"
          ) {
            updateAgentTimeline(agent, "running", chunk.message);
          } else if (event === "agent_progress") {
            updateAgentTimeline(agent, "running", chunk.message);
          } else if (
            event === "agent_complete" ||
            event === "decomposition_complete" ||
            event === "synthesis_complete"
          ) {
            updateAgentTimeline(agent, "completed", chunk.message);
          }
          // Continue to next chunk - timeline events are separate from tokens
          continue;
        }

        // Handle token events - STEP 3: Stream response tokens
        if (chunk.delta) {
          if (!firstTokenReceived) {
            // First token arrived - transition from thinking to streaming
            setIsThinking(false);
            setShowThinkingPanel(false); // Hide thinking panel when tokens start
            firstTokenReceived = true;
          }
          fullContent += chunk.delta;
          setStreamingMessage(fullContent);
          scrollToBottom();
        }

        // STEP 4: Finalize message when streaming completes
        if (chunk.final && chunk.message_id) {
          setStreamingMessageId(chunk.message_id);

          // Clear pending user message - it's now saved in conversation
          setPendingUserMessage(null);
          
          // Store files before clearing for completed message
          const filesForMessage = [...pendingUserFiles];
          setPendingUserFiles([]);

          // Add completed messages to local state (user + assistant)
          setCompletedMessages((prev) => [
            ...prev,
            {
              id: `user-${Date.now()}`,
              text: userMessage,
              isUser: true,
              metadata: { attachedFiles: filesForMessage },
            },
            {
              id: chunk.message_id,
              text: fullContent,
              isUser: false,
              metadata: {},
            },
          ]);

          // Clear streaming state
          setStreamingMessage("");
          setStreamingMessageId(null);

          // Auto-collapse timeline after 2 seconds
          setTimeout(() => {
            setTimelineCollapsed(true);
          }, 2000);
          break;
        }
      }
    } catch (error: any) {
      if (error.name === "AbortError") {
        console.log("Stream cancelled");
      } else {
        console.error("Error sending message:", error);
      }
      // Clear pending message and files on error
      setPendingUserMessage(null);
      setPendingUserFiles([]);
    } finally {
      setIsLoading(false);
      setIsThinking(false);
      setIsStreaming(false);
      setStreamingMessage("");
      setStreamingMessageId(null);
      setShowThinkingPanel(false); // Clear thinking panel
      abortControllerRef.current = null;
      
      // Refresh chats list to update "Recent Chats" with latest activity
      refreshChats(true).catch(console.error);
    }
  };

  const handleCancelStream = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
      setIsThinking(false);
      setStreamingMessage("");
    }
  };

  const chatTitle = currentConversation?.title || "Avalon";

  const hasActiveAgents = Object.values(agentTimeline).some(
    (state) => state.status === "running" || state.status === "pending"
  );
  const timelineVisible =
    isStreaming || hasActiveAgents || Object.keys(agentTimeline).length > 0;

  return (
    <div className="flex flex-col h-full">
      <TopBar chatTitle={chatTitle} />

      {timelineVisible && (
        <AgentTimeline
          timeline={agentTimeline}
          isVisible={timelineVisible}
          onToggle={() => setTimelineCollapsed(!timelineCollapsed)}
          isCollapsed={timelineCollapsed}
        />
      )}

      <ScrollArea className="flex-1 px-6">
        <div className="max-w-4xl mx-auto py-8" style={{ minHeight: "100%" }}>
          {messages.length === 0 && !isLoading && !streamingMessage && (
            <div className="text-center py-20">
              <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-blue-500 via-cyan-500 to-blue-600 flex items-center justify-center shadow-2xl shadow-blue-500/30">
                <Sparkles className="w-12 h-12 text-white" />
              </div>
              <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-400 via-cyan-400 to-blue-500 bg-clip-text text-transparent mb-3">
                {currentConversation ? "Ready to Research" : "Welcome to Avalon"}
              </h2>
              <p className="text-gray-400 text-lg max-w-2xl mx-auto leading-relaxed">
                {currentConversation 
                  ? "Ask me anything about pharmaceutical research, clinical trials, patents, market analysis, or competitive intelligence."
                  : "Click 'New Chat' in the sidebar to start a new research conversation."}
              </p>
            </div>
          )}

          {/* Render conversation messages - EXCLUDE pending message to avoid duplicates */}
          {messages.map((message) => {
            // Extract multi-agent data from metadata
            const workers =
              !message.isUser && message.metadata?.workers
                ? message.metadata.workers
                : undefined;
            const expert_graph_id =
              !message.isUser && message.metadata?.expert_graph_id
                ? message.metadata.expert_graph_id
                : undefined;
            const timeline =
              !message.isUser && message.metadata?.timeline
                ? message.metadata.timeline
                : undefined;

            return (
              <div key={message.id}>
                <MessageBubble 
                  message={message.text} 
                  isUser={message.isUser} 
                  attachedFiles={message.isUser ? message.metadata?.attachedFiles : undefined}
                />

                {/* Research Insights Table - shows real data if available, otherwise mock */}
                {!message.isUser && (
                  <div className="max-w-6xl mx-auto px-4">
                    <ResearchInsightsTable
                      insights={message.metadata?.research_insights}
                      useMockData={true}
                    />
                  </div>
                )}

                {!message.isUser &&
                  (workers || expert_graph_id || timeline) && (
                    <div className="max-w-4xl mx-auto">
                      <MultiAgentRenderer
                        workers={workers}
                        expert_graph_id={expert_graph_id}
                        timeline={timeline}
                      />
                    </div>
                  )}
              </div>
            );
          })}

          {/* Show pending user message ONLY if not in conversation yet */}
          {pendingUserMessage && (
            <div key="pending-user-message">
              <MessageBubble 
                message={pendingUserMessage} 
                isUser={true} 
                attachedFiles={pendingUserFiles}
              />
            </div>
          )}

          {/* Thinking Panel - PHI detection and routing decision (appears FIRST) */}
          {showThinkingPanel && routingMessage && (
            <div key="thinking-panel">
              <ThinkingPanel
                routingMessage={routingMessage}
                modeMessage={modeMessage}
                isVisible={showThinkingPanel}
              />
            </div>
          )}

          {/* Thinking indicator - appears UNDER thinking panel */}
          {isThinking && !streamingMessage && !showThinkingPanel && (
            <div key="thinking-indicator">
              <ThinkingIndicator />
            </div>
          )}

          {/* Data Source RAG indicator */}
          {dataSourceIndicator && (
            <div key="data-source-indicator" className="mb-3 max-w-4xl mx-auto">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 border border-blue-500/30 rounded-full">
                <FileText className="w-3.5 h-3.5 text-blue-400" />
                <span className="text-xs text-blue-300">{dataSourceIndicator}</span>
              </div>
            </div>
          )}

          {/* Streaming response - replaces thinking indicator */}
          {streamingMessage && (
            <div key="streaming-message">
              <StreamingMessageBubble message={streamingMessage} />
            </div>
          )}

          {isLoading && !isThinking && !streamingMessage && (
            <div className="flex items-center gap-4 mb-6">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 via-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
                <Loader2 className="w-5 h-5 text-white animate-spin" />
              </div>
              <div className="bg-gray-900/50 border border-gray-800 rounded-2xl px-5 py-4">
                <p className="text-sm text-gray-400">
                  Analyzing pharmaceutical databases and research sources...
                </p>
              </div>
            </div>
          )}

          <div ref={scrollRef} />
        </div>
      </ScrollArea>

      {/* Floating Buttons */}
      <div className="fixed bottom-24 right-8 z-50 flex items-center gap-3">
        {/* Report Generation Button */}
        {showReportButton && (
          <Button
            onClick={() => {
              console.log(
                "[REPORT_BUTTON] Opening reports page with data:",
                reportData
              );
              navigate("/reports");
              setShowReportButton(false);
            }}
            className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white px-6 py-6 rounded-full shadow-2xl shadow-green-500/50 flex items-center gap-3 text-base font-semibold transition-all duration-300 hover:scale-105 animate-in fade-in slide-in-from-bottom-4 duration-500"
          >
            <FileText className="w-5 h-5" />
            Generate Report
          </Button>
        )}
      </div>

      <ChatInput
        onSend={handleSendMessage}
        isLoading={isLoading}
        onCancel={handleCancelStream}
        isStreaming={isStreaming}
      />
    </div>
  );
}
