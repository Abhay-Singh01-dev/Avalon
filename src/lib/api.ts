import { useState } from "react";

type HttpMethod = "GET" | "POST" | "PATCH" | "DELETE";

type ToastVariant = "success" | "error" | "info";

type RequestOptions = {
  method?: HttpMethod;
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  retries?: number;
  retryDelayMs?: number;
};

export type ChatSummary = {
  id: string;
  title: string;
  project_id?: string | null;
  updated_at?: string;
};

export type Message = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: string;
  metadata?: Record<string, unknown>;
};

export type Conversation = ChatSummary & {
  messages: Message[];
};

export type Project = {
  id: string;
  name: string;
  description?: string;
  chat_ids?: string[];
  created_at?: string;
  updated_at?: string;
};

export type Report = {
  id: string;
  name: string;
  about?: string;
  query?: string;
  type: "pdf" | "csv" | "xlsx";
  created_at?: string;
  file_url?: string;
  isMock?: boolean;
  has_table?: boolean;
  size?: number;
};

export type GraphData = {
  nodes: Array<Record<string, unknown>>;
  edges: Array<Record<string, unknown>>;
  meta?: Record<string, unknown>;
};

export type GraphResponse = {
  graph_id?: string;
  graph?: GraphData;
} & GraphData;

export type SettingsPayload = {
  agentPersona?: string;
  responseStyle?: string;
  focusAreas?: Record<string, boolean>;
  dataSources?: Record<string, boolean>;
};

// Project RAG Types
export type ProjectFile = {
  id: string;
  project_id: string;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  status: 'uploaded' | 'processing' | 'indexed' | 'failed';
  extracted_text_preview?: string;
  chunk_count?: number;
  created_at?: string;
  error?: string;
};

export type ProjectLink = {
  id: string;
  project_id: string;
  url: string;
  title?: string;
  description?: string;
  enabled: boolean;
  fetched: boolean;
  created_at?: string;
};

export type RAGStatus = {
  project_rag: {
    enabled: boolean;
    description: string;
    requirement: string;
  };
  link_fetch: {
    enabled: boolean;
    description: string;
    requirement: string;
  };
  web_scraping: {
    enabled: boolean;
    description: string;
    requirement: string;
  };
  current_model: string;
  safe_for_healthcare: boolean;
  message: string;
};

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Response formatting instructions for concise, well-structured answers
const RESPONSE_FORMAT_INSTRUCTION = `
[RESPONSE FORMAT RULES - Follow strictly]
- Keep responses CONCISE and to-the-point
- Use clear HEADINGS (##) to organize sections
- Use BULLET POINTS (•) for lists, not paragraphs
- Maximum 2-3 sentences per bullet point
- For overviews: provide a brief summary (3-4 sentences max), then key points
- Avoid long paragraphs - break into digestible bullets
- Use bold (**text**) for key terms
- End with a brief conclusion if needed (1-2 sentences)
[END FORMAT RULES]

`;

const getDefaultHeaders = (
  customHeaders?: Record<string, string>
): Record<string, string> => {
  const headers: Record<string, string> = {};

  // Only add Content-Type if not FormData
  if (!customHeaders || !customHeaders["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  return { ...headers, ...customHeaders };
};

const showToast = (
  title: string,
  description: string,
  variant: ToastVariant = "info"
) => {
  // Placeholder toast implementation – can be wired to a UI system later.
  console[variant === "error" ? "error" : "log"](
    `[toast:${variant}] ${title}: ${description}`
  );
};

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

async function request<T>(
  path: string,
  {
    method = "GET",
    body,
    headers = {},
    signal,
    retries = 1,
    retryDelayMs = 500,
  }: RequestOptions = {}
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  let attempt = 0;
  while (true) {
    try {
      // Don't set Content-Type for FormData
      const requestHeaders =
        body instanceof FormData
          ? getDefaultHeaders({ ...headers })
          : getDefaultHeaders(headers);

      const response = await fetch(url, {
        method,
        headers: requestHeaders,
        body:
          body instanceof FormData
            ? body
            : body
            ? JSON.stringify(body)
            : undefined,
        signal,
      });

      if (!response.ok) {
        const message = await response.text();
        throw new Error(
          message || `Request failed with status ${response.status}`
        );
      }

      if (response.status === 204) {
        return undefined as T;
      }

      const data = (await response.json()) as T;
      return data;
    } catch (error) {
      attempt += 1;
      if (attempt > retries) {
        showToast("Request failed", (error as Error).message, "error");
        throw error;
      }
      await sleep(retryDelayMs * attempt);
    }
  }
}

// Helper to normalize conversation response (map _id to id)
const normalizeConversation = (conv: any): any => {
  if (!conv) return conv;
  return {
    ...conv,
    id: conv.id || conv._id,
    messages: conv.messages?.map((msg: any) => ({
      ...msg,
      id: msg.id || msg._id,
    })) || [],
  };
};

export const api = {
  chats: {
    list: async () => {
      const response = await request<{ conversations: any[] }>(
        "/api/chat/conversations?page=1&page_size=100"
      );
      return {
        ...response,
        conversations: response.conversations?.map(normalizeConversation) || [],
      };
    },
    get: async (id: string) => {
      const conv = await request<any>(`/api/chat/conversations/${id}`);
      return normalizeConversation(conv);
    },
    create: (payload: { title?: string; project_id?: string | null }) =>
      request<{ conversation_id: string; title: string }>(
        "/api/chat/conversations",
        {
          method: "POST",
          body: payload,
        }
      ),
    ask: (payload: {
      conversation_id?: string;
      message: string;
      project_id?: string;
      attachments?: string[]; // file_ids from uploaded files
    }) =>
      request<{ conversation_id: string; content: string }>("/api/chat/ask", {
        method: "POST",
        body: {
          ...payload,
          message: RESPONSE_FORMAT_INSTRUCTION + payload.message,
        },
        retries: 2,
      }),
    askStream: async function* (
      payload: {
        conversation_id?: string;
        message: string;
        project_id?: string;
        attachments?: string[]; // file_ids from uploaded files
      },
      signal?: AbortSignal
    ): AsyncGenerator<
      {
        delta?: string;
        final?: boolean;
        message_id?: string;
        error?: string;
        type?: string;
        event?: string;
        agent?: string;
        message?: string;
        report_ready?: boolean;
        report_data?: Record<string, any>;
        [key: string]: any;
      },
      void,
      unknown
    > {
      const url = `${BASE_URL}/api/chat/ask/stream`;
      const headers = getDefaultHeaders();

      // Prepend formatting instructions to ensure concise, well-structured responses
      const formattedPayload = {
        ...payload,
        message: RESPONSE_FORMAT_INSTRUCTION + payload.message,
      };

      const response = await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify(formattedPayload),
        signal,
      });

      if (!response.ok) {
        const message = await response.text();
        yield {
          error: message || `Request failed with status ${response.status}`,
        };
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        yield { error: "No response body" };
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";

      try {
        while (true) {
          const { done, value } = await reader.read();

          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.trim()) {
              try {
                const data = JSON.parse(line);
                // Handle timeline events (type: "timeline" or has "event" field)
                if (data.type === "thinking") {
                  // THINKING PANEL: PHI detection routing message (first event)
                  yield { type: "thinking", message: data.message };
                } else if (data.type === "routing") {
                  // ROUTING EVENT: Contains mode and routing decision
                  yield {
                    type: "routing",
                    mode: data.mode,
                    reason: data.reason,
                    detected_mode: data.detected_mode,
                    mode_reason: data.mode_reason
                  };
                } else if (data.type === "timeline" || data.event) {
                  yield data;
                } else if (data.type === "data_source_used") {
                  // DATA SOURCE RAG: Yield indicator when data sources are used
                  yield {
                    type: "data_source_used",
                    indicator: data.indicator,
                    categories: data.categories,
                    source_restriction: data.source_restriction
                  };
                } else if (data.type === "token" && data.delta) {
                  yield { delta: data.delta };
                } else if (data.delta) {
                  // Legacy format support
                  yield { delta: data.delta };
                } else if (data.report_ready) {
                  // REPORT GENERATION SIGNAL: Yield report_ready flag
                  yield { report_ready: true, report_data: data.report_data };
                } else if (data.final) {
                  yield data;
                  return;
                } else if (data.error) {
                  yield data;
                  return;
                } else {
                  // Other structured data
                  yield data;
                }
              } catch (e) {
                // Skip invalid JSON lines
                continue;
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    },
    rename: (id: string, payload: { title: string }) =>
      request(`/api/chat/conversations/${id}/rename`, {
        method: "POST",
        body: payload,
      }),
    delete: (id: string) =>
      request(`/api/chat/conversations/${id}`, {
        method: "DELETE",
      }),
    assignProject: (id: string, payload: { project_id: string | null }) =>
      request(`/api/chat/conversations/${id}/project`, {
        method: "POST",
        body: payload,
      }),
    createGroupChat: (id: string) =>
      request<{
        status: string;
        message: string;
        conversation_id: string;
        invite_code: string;
        invite_link: string;
      }>(`/api/chat/conversations/${id}/group-chat`, {
        method: "POST",
      }),
    getByInviteCode: (inviteCode: string) =>
      request<{
        status: string;
        conversation_id: string;
        title: string;
        created_at: string;
        participants_count: number;
      }>(`/api/chat/invite/${inviteCode}`),
  },
  projects: {
    list: () => request<{ projects: Project[] }>("/api/projects"),
    create: (payload: { name: string; description?: string }) =>
      request<Project>("/api/projects", { method: "POST", body: payload }),
    rename: (id: string, payload: { name: string; description?: string }) =>
      request<Project>(`/api/projects/${id}`, {
        method: "PATCH",
        body: payload,
      }),
    remove: (id: string) =>
      request(`/api/projects/${id}`, { method: "DELETE" }),
    getChats: (id: string) =>
      request<{ chats: ChatSummary[] }>(`/api/projects/${id}/chats`),
    addChat: (id: string, payload: { chat_id: string }) =>
      request(`/api/projects/${id}/add_chat`, {
        method: "POST",
        body: payload,
      }),
    removeChat: (id: string, payload: { chat_id: string }) =>
      request(`/api/projects/${id}/remove_chat`, {
        method: "POST",
        body: payload,
      }),
  },
  uploads: {
    uploadFile: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch(`${BASE_URL}/api/upload/document`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        const message = await response.text();
        showToast("Upload failed", message, "error");
        throw new Error(message);
      }
      return (await response.json()) as { file_id: string; name: string };
    },
  },
  reports: {
    list: (params?: { page?: number; page_size?: number; type?: string }) => {
      const query = new URLSearchParams();
      if (params?.page) query.append("page", String(params.page));
      if (params?.page_size)
        query.append("page_size", String(params.page_size));
      if (params?.type) query.append("type", params.type);
      const qs = query.toString();
      return request<{ reports: Report[]; total: number }>(
        `/api/reports${qs ? `?${qs}` : ""}`
      );
    },
    get: (id: string) => request<Report>(`/api/reports/${id}`),
    delete: (id: string) => request(`/api/reports/${id}`, { method: "DELETE" }),
    generate: (payload: {
      report_type?: string;
      parameters?: Record<string, unknown>;
      format?: string;
      title?: string;
      description?: string;
      conversation_id?: string;
    }) =>
      request<{ report_id: string; status: string; message?: string }>(
        "/api/reports/generate",
        {
          method: "POST",
          body: payload,
        }
      ),
  },
  graph: {
    get: (id: string) => request<GraphResponse>(`/api/graph/${id}`),
    build: (payload: { query: string; signals: Record<string, unknown> }) =>
      request(`/api/graph/build`, { method: "POST", body: payload }),
  },
  auth: {
    login: (email: string, password: string) => {
      const formData = new FormData();
      formData.append("username", email);
      formData.append("password", password);
      return request<{
        access_token: string;
        token_type: string;
        refresh_token: string;
      }>("/api/auth/login", {
        method: "POST",
        body: formData,
      });
    },
    register: (payload: {
      email: string;
      password: string;
      full_name: string;
      role?: "user" | "admin";
    }) =>
      request<{ id: string; email: string; full_name: string; role: string }>(
        "/api/auth/register",
        {
          method: "POST",
          body: payload,
        }
      ),
    me: () =>
      request<{ id: string; email: string; full_name: string; role: string }>(
        "/api/auth/me"
      ),
    refresh: (refreshToken: string) =>
      request<{
        access_token: string;
        token_type: string;
        refresh_token: string;
      }>("/api/auth/refresh", {
        method: "POST",
        body: { refresh_token: refreshToken },
      }),
  },
  settings: {
    get: () => request<SettingsPayload>("/api/settings"),
    update: (payload: SettingsPayload) =>
      request("/api/settings", { method: "PATCH", body: payload }),
  },
  admin: {
    getStats: () => {
      return request<{
        conversations: number;
        messages: number;
        projects: number;
        reports: number;
        status: string;
      }>(`/api/admin/stats`);
    },
  },
  // Project RAG endpoints
  projectFiles: {
    // Get RAG system status
    getRagStatus: () => request<RAGStatus>("/api/projects/rag/status"),
    
    // Upload file to project
    upload: async (projectId: string, file: File): Promise<ProjectFile> => {
      const formData = new FormData();
      formData.append("file", file);
      
      const headers: Record<string, string> = {};
      const token = localStorage.getItem("access_token");
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      
      const response = await fetch(`${BASE_URL}/api/projects/${projectId}/upload`, {
        method: "POST",
        headers,
        body: formData,
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(error.detail || "Upload failed");
      }
      
      return response.json();
    },
    
    // Get all files for a project
    list: (projectId: string) => 
      request<{ files: ProjectFile[]; total: number; rag_enabled: boolean; rag_status_message: string }>(
        `/api/projects/${projectId}/files`
      ),
    
    // Get file preview
    preview: (projectId: string, fileId: string) =>
      request<{
        id: string;
        filename: string;
        file_type: string;
        status: string;
        extracted_text: string;
        chunk_count: number;
        rag_enabled: boolean;
      }>(`/api/projects/${projectId}/files/${fileId}/preview`),
    
    // Delete file
    delete: (projectId: string, fileId: string) =>
      request(`/api/projects/${projectId}/files/${fileId}`, { method: "DELETE" }),
    
    // Reindex project documents
    reindex: (projectId: string) =>
      request<{
        status: string;
        message: string;
        reindexed_count: number;
        errors?: string[];
        rag_enabled: boolean;
      }>(`/api/projects/${projectId}/reindex`, { method: "POST" }),
  },
  projectLinks: {
    // Add link to project
    add: (projectId: string, data: { url: string; title?: string; description?: string }) =>
      request<ProjectLink>(`/api/projects/${projectId}/add-link`, {
        method: "POST",
        body: data,
      }),
    
    // Get all links for a project
    list: (projectId: string) =>
      request<{ links: ProjectLink[]; total: number; link_fetch_enabled: boolean; message: string }>(
        `/api/projects/${projectId}/links`
      ),
    
    // Delete link
    delete: (projectId: string, linkId: string) =>
      request(`/api/projects/${projectId}/links/${linkId}`, { method: "DELETE" }),
  },
  // Data Source RAG endpoints
  dataSources: {
    // Get RAG status and statistics
    getStatus: () => request<{
      status: string;
      rag_enabled: boolean;
      model: string;
      stats: {
        total_chunks: number;
        total_files: number;
        categories: Record<string, number>;
        sources: Record<string, number>;
        last_updated: string | null;
      };
    }>("/api/data_sources/status"),
    
    // Upload file to data source
    upload: async (sourceId: string, sourceName: string, file: File, category?: string): Promise<{
      status: string;
      file_id: string;
      file_name: string;
      source_id: string;
      source_name: string;
      category: string;
      chunk_count: number;
      embeddings_generated: boolean;
    }> => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("source_id", sourceId);
      formData.append("source_name", sourceName);
      if (category) {
        formData.append("category", category);
      }
      
      const headers: Record<string, string> = {};
      const token = localStorage.getItem("access_token");
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      
      const response = await fetch(`${BASE_URL}/api/data_sources/upload`, {
        method: "POST",
        headers,
        body: formData,
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(error.detail || "Upload failed");
      }
      
      return response.json();
    },
    
    // List all data sources
    list: () => request<{
      status: string;
      sources: Array<{
        source_id: string;
        source_name: string;
        chunk_count: number;
        categories: string[];
        last_updated: string | null;
      }>;
      total_sources: number;
      total_chunks: number;
      total_files: number;
      rag_enabled: boolean;
    }>("/api/data_sources/list"),
    
    // Get files for a specific source
    getFiles: (sourceId: string) => request<{
      status: string;
      source_id: string;
      files: Array<{
        file_id: string;
        file_name: string;
        category: string;
        chunk_count: number;
        indexed: boolean;
        created_at: string | null;
      }>;
      total_files: number;
    }>(`/api/data_sources/${sourceId}/files`),
    
    // Search data sources
    search: (query: string, category?: string, sourceId?: string, topK?: number) => {
      const params = new URLSearchParams({ query });
      if (category) params.append("category", category);
      if (sourceId) params.append("source_id", sourceId);
      if (topK) params.append("top_k", String(topK));
      
      return request<{
        status: string;
        query: string;
        results: Array<{
          chunk_id: string;
          text: string;
          source_id: string;
          source_name: string;
          category: string;
          similarity: number;
        }>;
        total_results: number;
        rag_enabled: boolean;
      }>(`/api/data_sources/search?${params.toString()}`);
    },
    
    // Delete a data source
    delete: (sourceId: string) =>
      request(`/api/data_sources/${sourceId}`, { method: "DELETE" }),
    
    // Delete a specific file
    deleteFile: (sourceId: string, fileId: string) =>
      request(`/api/data_sources/${sourceId}/files/${fileId}`, { method: "DELETE" }),
    
    // Rebuild index
    rebuildIndex: (sourceId?: string) => {
      const url = sourceId 
        ? `/api/data_sources/rebuild-index?source_id=${sourceId}`
        : "/api/data_sources/rebuild-index";
      return request<{
        status: string;
        message: string;
        files_processed: number;
        total_chunks: number;
        errors: number;
      }>(url, { method: "POST" });
    },
    
    // Get available categories
    getCategories: () => request<{
      status: string;
      categories: string[];
    }>("/api/data_sources/categories"),
  },
};

export const useApiRequest = <T>(fn: () => Promise<T>) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<T | null>(null);

  const execute = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fn();
      setData(result);
      return result;
    } catch (err) {
      setError((err as Error).message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { execute, loading, error, data };
};
