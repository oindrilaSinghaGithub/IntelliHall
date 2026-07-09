"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { AuthGuard } from "@/components/shared/auth-guard";
import { useAuthStore } from "@/store/auth-store";

interface AdminLayoutProps {
  children: React.ReactNode;
}

function AdminRoleGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user } = useAuthStore();

  useEffect(() => {
    if (user && user.role !== "hall_admin") {
      router.replace("/dashboard");
    }
  }, [user, router]);

  if (!user || user.role !== "hall_admin") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return <>{children}</>;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  return (
    <AuthGuard>
      <AdminRoleGuard>{children}</AdminRoleGuard>
    </AuthGuard>
  );
}
