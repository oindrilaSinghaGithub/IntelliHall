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
      partialize: (state) => ({          // only persist user, not functions
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
);
