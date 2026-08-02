import type {
  Application,
  ApplicationListResponse,
  AtsSource,
  AuthResponse,
  AuthStatus,
  GoogleLinksResponse,
  JobSearchRequest,
  JobSearchResponse,
  ResumeProfile,
  JobListing,
  SavedSearch,
  SavedSearchListResponse,
  SearchStatus,
  User,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const TOKEN_KEY = "vacancylane_token";
export const AUTH_EXPIRED_EVENT = "vacancylane:auth-expired";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setAccessToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

function notifyAuthExpired() {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAccessToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text();
    let message = text || `Request failed: ${res.status}`;
    try {
      const data = JSON.parse(text);
      if (data?.detail) {
        message =
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail);
      }
    } catch {
      // keep raw text
    }
    if (res.status === 401 && token) {
      // Drop the dead token so the next page load does not keep a zombie session.
      setAccessToken(null);
      notifyAuthExpired();
    }
    throw new Error(message);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  getAtsSources: () => request<AtsSource[]>("/ats-sources"),
  getSearchStatus: () => request<SearchStatus>("/search/status"),
  getAuthStatus: () => request<AuthStatus>("/auth/status"),
  loginWithGoogle: (idToken: string) =>
    request<AuthResponse>("/auth/google", {
      method: "POST",
      body: JSON.stringify({ id_token: idToken }),
    }),
  getMe: () => request<User>("/auth/me"),
  listApplications: () => request<ApplicationListResponse>("/applications"),
  applyToJob: (data: {
    job_url: string;
    job_title: string;
    company?: string | null;
    location?: string | null;
    source?: string | null;
    source_name?: string | null;
  }) =>
    request<Application>("/applications", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  deleteApplication: (id: number) =>
    request<void>(`/applications/${id}`, { method: "DELETE" }),
  updateApplication: (
    id: number,
    data: { status?: string; notes?: string | null }
  ) =>
    request<Application>(`/applications/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  listSearchHistory: () => request<SavedSearchListResponse>("/history"),
  getSearchHistoryById: (id: string) => request<SavedSearch>(`/history/${id}`),
  saveSearch: (data: {
    role: string;
    alternate_role?: string | null;
    location_label?: string | null;
    skills?: string | null;
    company?: string | null;
    experience_bands?: string[];
    sources?: string[];
    payload: JobSearchRequest;
    result_count: number;
    results_json?: JobListing[];
  }) =>
    request<SavedSearch>("/history", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  deleteSearch: (id: string) =>
    request<void>(`/history/${id}`, { method: "DELETE" }),
  searchJobs: (data: JobSearchRequest) =>
    request<JobSearchResponse>("/search", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getGoogleLinks: (data: JobSearchRequest) =>
    request<GoogleLinksResponse>("/search/google-links", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  parseResume: async (file: File) => {
    const token = getAccessToken();
    const body = new FormData();
    body.append("file", file);
    const res = await fetch(`${API_BASE}/search/from-resume`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      body,
    });
    if (!res.ok) {
      let message = `Request failed: ${res.status}`;
      try {
        const data = await res.json();
        message = data.detail || message;
      } catch {
        message = (await res.text()) || message;
      }
      throw new Error(
        typeof message === "string" ? message : JSON.stringify(message)
      );
    }
    return res.json() as Promise<ResumeProfile>;
  },
};
