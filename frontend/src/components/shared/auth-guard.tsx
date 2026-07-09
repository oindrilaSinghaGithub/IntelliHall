"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { useAuthStore } from "@/store/auth-store";
import { getToken } from "@/services/api-client";
import { getMe } from "@/services/auth";

interface AuthGuardProps {
  children: React.ReactNode;
}

let hasRefetchedProfile = false;

/**
 * Wraps protected pages.
 *
 * On mount:
 *  - If there is no JWT in localStorage → redirect to /login.
 *  - If there is a JWT but no user in the store (e.g. hard refresh) →
 *    re-fetch GET /api/v1/auth/me to rehydrate the store, then render.
 *  - If there is a JWT and a user in the store → render immediately,
 *    and sync user details once in the background to update cache.
 */
export function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter();
  const { user, isAuthenticated, setUser, clearAuth } = useAuthStore();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    async function check() {
      const token = getToken();

      if (!token) {
        clearAuth();
        router.replace("/login");
        return;
      }

      // Token present but store empty (hard refresh / SSR hydration gap)
      if (!isAuthenticated || !user) {
        try {
          const me = await getMe();
          setUser(me);
          hasRefetchedProfile = true;
        } catch {
          clearAuth();
          router.replace("/login");
          return;
        }
      } else if (!hasRefetchedProfile) {
        // Hydrated from cache: sync once in the background to update cached localStorage values
        getMe()
          .then((me) => {
            setUser(me);
            hasRefetchedProfile = true;
          })
          .catch(() => {
            hasRefetchedProfile = true;
          });
      }

      setChecking(false);
    }

    check();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return <>{children}</>;
}
