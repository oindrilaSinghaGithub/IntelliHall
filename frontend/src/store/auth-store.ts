import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { User } from "@/types/auth";

// ---------------------------------------------------------------------------
// Auth store — persisted in localStorage via zustand/middleware/persist
// ---------------------------------------------------------------------------

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;

  // Actions
  setUser: (user: User) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,

      setUser: (user: User) =>
        set({ user, isAuthenticated: true }),

      clearAuth: () =>
        set({ user: null, isAuthenticated: false }),
    }),
    {
      name: "intellihall_auth",          // localStorage key for the store
      version: 1,                        // bump when User shape changes — forces re-login
      partialize: (state) => ({          // only persist user, not functions
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
      migrate: (persisted: unknown, fromVersion: number) => {
        // v0 → v1: hall_verification_status was added.
        // If the old cached user lacks this field, clear it so AuthGuard
        // re-fetches a fresh user from /api/v1/auth/me instead of rendering
        // stale data that breaks the verification banner logic.
        if (fromVersion < 1) {
          const old = persisted as { user?: Partial<User>; isAuthenticated?: boolean };
          if (old?.user && !old.user.hall_verification_status) {
            return { user: null, isAuthenticated: false };
          }
        }
        return persisted as AuthState;
      },
    },
  ),
);
