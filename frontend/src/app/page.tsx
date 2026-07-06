"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { useAuthStore } from "@/store/auth-store";
import { getToken } from "@/services/api-client";

/**
 * Root route ( / ) — redirects based on auth state:
 *  - Authenticated  → /dashboard
 *  - Unauthenticated → /login
 *
 * The landing page (Hero, Features, Footer) remains accessible at /home
 * or directly from the Navbar.
 */
export default function RootPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    const token = getToken();
    if (token && isAuthenticated) {
      router.replace("/dashboard");
    } else {
      router.replace("/login");
    }
  }, [isAuthenticated, router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
    </div>
  );
}
