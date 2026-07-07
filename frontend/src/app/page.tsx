"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { getToken } from "@/services/api-client";

/**
 * Root route ( / ) — redirects based on JWT presence in localStorage.
 *
 * Why we check the token directly instead of useAuthStore().isAuthenticated:
 *   Zustand's persist middleware rehydrates localStorage asynchronously on
 *   the first render. During that gap, isAuthenticated is always `false`
 *   even when the user has a valid JWT, causing a spurious redirect to /login.
 *   Reading the token directly from localStorage is synchronous and correct.
 *
 *   The actual session validity is confirmed by AuthGuard (which calls /me).
 */
export default function RootPage() {
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    if (token) {
      router.replace("/dashboard");
    } else {
      router.replace("/login");
    }
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
    </div>
  );
}
