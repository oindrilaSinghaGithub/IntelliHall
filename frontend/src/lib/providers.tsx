"use client";

import { useEffect, useState, type ReactNode } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
import { Toaster } from "sonner";

import { createQueryClient } from "@/lib/query-client";
import { useAuthStore } from "@/store/auth-store";
import { getToken } from "@/services/api-client";
import { getMe } from "@/services/auth";

interface AppProvidersProps {
  children: ReactNode;
}

/**
 * Root provider that wraps the entire application.
 *
 * On first render it silently tries to rehydrate the auth store
 * from localStorage (token → GET /me) so that a hard refresh
 * doesn't log the user out.
 */
export function AppProviders({ children }: AppProvidersProps) {
  const [queryClient] = useState(createQueryClient);
  const { setUser, clearAuth, isAuthenticated, user } = useAuthStore();

  // Rehydrate on app boot
  useEffect(() => {
    const token = getToken();
    if (token && (!isAuthenticated || !user)) {
      getMe()
        .then(setUser)
        .catch(() => {
          clearAuth();
        });
    }
    // Only run once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem disableTransitionOnChange>
      <QueryClientProvider client={queryClient}>
        {children}
        <Toaster position="top-right" richColors closeButton />
      </QueryClientProvider>
    </ThemeProvider>
  );
}
