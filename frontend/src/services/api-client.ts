import axios, { type AxiosError } from "axios";
import { API_BASE_URL } from "@/constants";

// ---------------------------------------------------------------------------
// JWT helpers — localStorage persistence
// ---------------------------------------------------------------------------

const TOKEN_KEY = "intellihall_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30_000,
});

// Request interceptor: inject Bearer token automatically
apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: on 401 clear token and redirect to /login
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      removeToken();
      // Only redirect when in the browser and not already on /login
      if (
        typeof window !== "undefined" &&
        !window.location.pathname.startsWith("/login")
      ) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

// ---------------------------------------------------------------------------
// Error helper — extract a human-readable message from FastAPI error shapes
// ---------------------------------------------------------------------------

export function extractApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;
    if (!data) return error.message || "Network error. Please try again.";

    if (typeof data.detail === "string") return data.detail;

    if (Array.isArray(data.detail)) {
      return data.detail.map((e: { msg: string }) => e.msg).join(", ");
    }
  }
  if (error instanceof Error) return error.message;
  return "An unexpected error occurred.";
}
