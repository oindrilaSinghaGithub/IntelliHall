"use client";

import { Building2, LogOut, ClipboardList, LayoutDashboard } from "lucide-react";
import Link from "next/link";

import { AuthGuard } from "@/components/shared/auth-guard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/use-auth";

export default function DashboardPage() {
  const { user, signOut } = useAuth();

  return (
    <AuthGuard>
      <div className="flex min-h-screen flex-col bg-background">
        {/* Top nav */}
        <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur-xl">
          <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
            <Link href="/dashboard" className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                <Building2 className="h-4 w-4 text-primary" />
              </div>
              <span className="text-sm font-semibold tracking-tight">IntelliHall</span>
            </Link>

            <div className="flex items-center gap-3">
              <div className="hidden text-right sm:block">
                <p className="text-sm font-medium">{user?.name}</p>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
              </div>
              <Badge variant={user?.role === "hall_admin" ? "default" : "secondary"}>
                {user?.role === "hall_admin" ? "Hall Admin" : "Student"}
              </Badge>
              <Button
                variant="ghost"
                size="sm"
                onClick={signOut}
                className="gap-2 text-muted-foreground hover:text-foreground"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Sign out</span>
              </Button>
            </div>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1">
          <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
            {/* Welcome banner */}
            <div className="mb-10 rounded-2xl border border-border/50 bg-card p-8 shadow-sm">
              <div className="flex items-start gap-4">
                <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-primary/10">
                  <LayoutDashboard className="h-7 w-7 text-primary" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold">
                    Welcome back, {user?.name?.split(" ")[0]}! 👋
                  </h1>
                  <p className="mt-1 text-muted-foreground">
                    {user?.role === "hall_admin"
                      ? "You are logged in as a Hall Administrator. Complaint management tools will appear here."
                      : "You are logged in as a Student. You can raise and track maintenance complaints here."}
                  </p>
                  {user?.hall_id ? (
                    <p className="mt-2 text-xs text-muted-foreground">
                      Hall ID: <span className="font-mono text-foreground/70">{user.hall_id}</span>
                    </p>
                  ) : (
                    <p className="mt-2 rounded-md bg-amber-500/10 px-3 py-1.5 text-xs text-amber-600 dark:text-amber-400 inline-block">
                      ⚠ You are not yet assigned to a hall. Contact your Hall Admin.
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Placeholder cards */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {[
                {
                  icon: ClipboardList,
                  title: "Complaints",
                  description:
                    user?.role === "hall_admin"
                      ? "View and manage all complaints in your hall."
                      : "Raise a new complaint or track your existing ones.",
                  coming: true,
                },
                {
                  icon: Building2,
                  title: "Hall Management",
                  description: "View hall information and assigned residents.",
                  coming: true,
                },
              ].map((card) => (
                <div
                  key={card.title}
                  className="group relative rounded-xl border border-border/50 bg-card p-6 shadow-sm transition-all hover:border-primary/30 hover:shadow-md"
                >
                  <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 transition-colors group-hover:bg-primary/15">
                    <card.icon className="h-5 w-5 text-primary" />
                  </div>
                  <h3 className="font-semibold">{card.title}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">{card.description}</p>
                  {card.coming && (
                    <span className="mt-3 inline-block rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium text-secondary-foreground">
                      Coming soon
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
