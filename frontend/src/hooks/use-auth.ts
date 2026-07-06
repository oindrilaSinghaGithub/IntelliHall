"use client";

import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { getMe, login, register } from "@/services/auth";
import { getToken, removeToken, setToken } from "@/services/api-client";
import { useAuthStore } from "@/store/auth-store";
import { extractApiError } from "@/services/api-client";
import type { LoginRequest, RegisterRequest } from "@/types/auth";

// ---------------------------------------------------------------------------
// useAuth — the single hook every component should use for auth operations
// ---------------------------------------------------------------------------

export function useAuth() {
  const router = useRouter();
  const { user, isAuthenticated, setUser, clearAuth } = useAuthStore();

  // ------------------------------------------------------------------
  // Fetch and store the current user from the backend
  // ------------------------------------------------------------------

  async function fetchCurrentUser() {
    const token = getToken();
    if (!token) return null;
    try {
      const me = await getMe();
      setUser(me);
      return me;
    } catch {
      removeToken();
      clearAuth();
      return null;
    }
  }

  // ------------------------------------------------------------------
  // Login: get token → store token → fetch user → redirect
  // ------------------------------------------------------------------

  async function signIn(data: LoginRequest): Promise<void> {
    const { access_token } = await login(data);
    setToken(access_token);
    const me = await getMe();
    setUser(me);
    toast.success(`Welcome back, ${me.name}!`);
    router.push("/dashboard");
  }

  // ------------------------------------------------------------------
  // Register: get token + user → store → redirect
  // ------------------------------------------------------------------

  async function signUp(data: RegisterRequest): Promise<void> {
    const { access_token, user: newUser } = await register(data);
    setToken(access_token);
    setUser(newUser);
    toast.success(`Account created! Welcome, ${newUser.name}!`);
    router.push("/dashboard");
  }

  // ------------------------------------------------------------------
  // Logout: clear token + store → redirect
  // ------------------------------------------------------------------

  function signOut(): void {
    removeToken();
    clearAuth();
    toast.success("You've been signed out.");
    router.push("/login");
  }

  return {
    user,
    isAuthenticated,
    fetchCurrentUser,
    signIn,
    signUp,
    signOut,
    extractApiError,
  };
}
