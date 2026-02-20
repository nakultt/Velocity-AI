/**
 * API Client for Velocity AI Backend
 * Handles all HTTP requests to the FastAPI backend
 */

import { APP_CONFIG } from '@/config/app.config';

// API Base URL
const API_BASE_URL = APP_CONFIG.api.baseUrl;

// ============== Types ==============

export interface User {
  id: number;
  email: string;
  name?: string;
  token?: string;
  created_at?: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  requires_approval: boolean;
  proposed_action?: Record<string, unknown>;
  sources: string[];
}

export interface ApiError {
  detail: string;
  error_code?: string;
}

export interface Conversation {
  id: number;
  title: string;
  owner_id: number;
  created_at: string;
  updated_at?: string;
}

export interface ConversationList {
  conversations: Conversation[];
  total: number;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface IntegrationStatus {
  service: string;
  connected: boolean;
  last_synced: string | null;
  scopes: string[];
}

// ============== Helper Functions ==============

function getAuthToken(): string | null {
  const localUser = localStorage.getItem(APP_CONFIG.storageKeys.user);
  if (localUser) {
    try {
      const parsed = JSON.parse(localUser);
      return parsed.token || null;
    } catch {
      return null;
    }
  }
  
  const sessionUser = sessionStorage.getItem(APP_CONFIG.storageKeys.user);
  if (sessionUser) {
    try {
      const parsed = JSON.parse(sessionUser);
      return parsed.token || null;
    } catch {
      return null;
    }
  }
  
  return null;
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken();

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({
      detail: `Request failed with status ${response.status}`,
    }));
    throw new Error(error.detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// ============== Auth API ==============

export async function signup(
  email: string,
  password: string,
  name?: string
): Promise<User> {
  return apiRequest<User>("/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password, name }),
  });
}

export async function login(
  email: string, 
  password: string,
  rememberMe: boolean = false
): Promise<User> {
  return apiRequest<User>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password, remember_me: rememberMe }),
  });
}

export interface UserUpdate {
  email?: string;
  password?: string;
  name?: string;
}

export async function updateUser(userId: number, data: UserUpdate): Promise<User> {
  return apiRequest<User>(`/auth/user/${userId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

// ============== Chat API ==============

export async function sendChatMessage(
  message: string,
  mode: string = "personal",
  conversationId?: string
): Promise<ChatResponse> {
  return apiRequest<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({
      message,
      mode,
      conversation_id: conversationId,
    }),
  });
}

// ============== Conversations API ==============

export async function createConversation(
  userId: number,
  title?: string
): Promise<Conversation> {
  return apiRequest<Conversation>("/api/conversations", {
    method: "POST",
    body: JSON.stringify({ user_id: userId, title }),
  });
}

export async function getUserConversations(
  userId: number
): Promise<ConversationList> {
  return apiRequest<ConversationList>(`/api/conversations/${userId}`);
}

export async function getConversationMessages(
  conversationId: number
): Promise<Message[]> {
  return apiRequest<Message[]>(`/api/conversations/${conversationId}/messages`);
}

export async function updateConversationTitle(
  conversationId: number,
  title: string
): Promise<Conversation> {
  return apiRequest<Conversation>(`/api/conversations/${conversationId}`, {
    method: "PUT",
    body: JSON.stringify({ title }),
  });
}

export async function deleteConversation(
  conversationId: number
): Promise<void> {
  return apiRequest<void>(`/api/conversations/${conversationId}`, {
    method: "DELETE",
  });
}

// ============== Integrations API ==============

export async function getIntegrationStatus(): Promise<IntegrationStatus[]> {
  return apiRequest<IntegrationStatus[]>("/api/integrations/status");
}

export function getGoogleConnectUrl(service: string = "google"): string {
  return `${API_BASE_URL}/api/integrations/google/connect?service=${service}`;
}

// ============== Health Check ==============

export async function healthCheck(): Promise<{
  status: string;
  service: string;
}> {
  return apiRequest<{ status: string; service: string }>("/health");
}

// ============== Projects (Workspace) ==============

export interface Project {
  id: string;
  name: string;
  status: string;
  progress: number;
  description: string;
  team_members: string[];
  last_updated: string;
  tech_stack: string[];
}

export interface UpdateFeedItem {
  id: string;
  message: string;
  source: string;
  timestamp: string;
  project: string | null;
  verified: boolean;
}

export interface Priority {
  id: string;
  title: string;
  urgency: string;
  project: string;
  assigned_to: string | null;
  ai_reasoning: string;
}

export interface ProjectDetail {
  project: Project;
  activities: UpdateFeedItem[];
  priorities: Priority[];
}

export async function getProjects(): Promise<Project[]> {
  return apiRequest<Project[]>("/api/projects");
}

export async function getProjectDetail(projectId: string): Promise<ProjectDetail> {
  return apiRequest<ProjectDetail>(`/api/projects/${projectId}`);
}

export async function getPriorities(): Promise<Priority[]> {
  return apiRequest<Priority[]>("/api/priorities");
}

// ============== AI Activity Log ==============

export interface ActivityLogEntry {
  id: string;
  timestamp: string;
  action: string;
  source: string;
  mode: string;
  project: string | null;
  details: string | null;
}

export async function getActivityLog(mode?: string): Promise<ActivityLogEntry[]> {
  const query = mode ? `?mode=${mode}` : "";
  return apiRequest<ActivityLogEntry[]>(`/api/activity-log${query}`);
}
