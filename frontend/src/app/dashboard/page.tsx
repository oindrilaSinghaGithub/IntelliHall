"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Building2, LogOut, ClipboardList, LayoutDashboard, Plus, ArrowRight } from "lucide-react";
import Link from "next/link";

import { AuthGuard } from "@/components/shared/auth-guard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/use-auth";
import { useComplaints } from "@/hooks/use-complaints";
import { ComplaintCard } from "@/components/shared/complaint-card";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function DashboardPage() {
  const router = useRouter();
  const { user, signOut } = useAuth();

  // Redirect admin users to their dedicated dashboard
  useEffect(() => {
    if (user && user.role === "hall_admin") {
      router.replace("/dashboard/admin");
    }
  }, [user, router]);

  // Fetch latest 3 complaints for student
  const isStudent = user?.role === "student";
  const { data: recentComplaints, isLoading: isComplaintsLoading } = useComplaints(
    isStudent
      ? {
          page: 1,
          page_size: 3,
          sort_by: "created_at",
          sort_order: "desc",
        }
      : { page: 1, page_size: 1 } // dummy/not used for admins
  );

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
                      Hall of Residence:{" "}
                      <span className="font-semibold text-foreground">
                        {user.hall_name || "Loading..."}
                      </span>
                    </p>
                  ) : (
                    <p className="mt-2 rounded-md bg-amber-500/10 px-3 py-1.5 text-xs text-amber-600 dark:text-amber-400 inline-block">
                      ⚠ You are not yet assigned to a hall. Contact your Hall Admin.
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Student View vs Admin View */}
            {isStudent ? (
              <div className="grid gap-6 md:grid-cols-3">
                {/* Actions and Info column */}
                <div className="space-y-6 md:col-span-1">
                  {/* Complaints Control Panel */}
                  <Card className="border border-border/50 bg-card">
                    <CardHeader>
                      <CardTitle className="text-lg font-bold flex items-center gap-2">
                        <ClipboardList className="h-5 w-5 text-primary" />
                        Complaints
                      </CardTitle>
                      <CardDescription>
                        Raise a new maintenance complaint or manage existing ones.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="flex flex-col gap-3">
                      <Button asChild className="w-full gap-1.5 shadow-xs">
                        <Link href="/dashboard/complaints/new">
                          <Plus className="h-4 w-4" />
                          Raise Complaint
                        </Link>
                      </Button>
                      <Button asChild variant="outline" className="w-full gap-1.5">
                        <Link href="/dashboard/complaints">
                          View My Complaints
                        </Link>
                      </Button>
                    </CardContent>
                  </Card>

                  {/* Hall Management Placeholder */}
                  <div className="group relative rounded-xl border border-border/50 bg-card p-6 shadow-xs transition-all hover:border-primary/30">
                    <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 transition-colors group-hover:bg-primary/15">
                      <Building2 className="h-5 w-5 text-primary" />
                    </div>
                    <h3 className="font-semibold text-sm">Hall Management</h3>
                    <p className="mt-1 text-xs text-muted-foreground">
                      View hall information and assigned residents.
                    </p>
                    <span className="mt-3 inline-block rounded-full bg-secondary px-2.5 py-0.5 text-[10px] font-medium text-secondary-foreground">
                      Coming soon
                    </span>
                  </div>
                </div>

                {/* Recent Complaints Column */}
                <div className="md:col-span-2 space-y-4">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-bold tracking-tight">Recent Complaints</h2>
                    {recentComplaints && recentComplaints.items.length > 0 && (
                      <Link
                        href="/dashboard/complaints"
                        className="inline-flex items-center text-xs font-medium text-primary hover:underline gap-1"
                      >
                        View all
                        <ArrowRight className="h-3 w-3" />
                      </Link>
                    )}
                  </div>

                  {isComplaintsLoading ? (
                    <LoadingSkeleton variant="list" count={3} />
                  ) : !recentComplaints || recentComplaints.items.length === 0 ? (
                    <div className="rounded-xl border border-dashed border-border/80 bg-card/50 p-8 text-center shadow-xs">
                      <p className="text-sm font-medium text-muted-foreground">
                        No complaints raised yet.
                      </p>
                      <p className="text-xs text-muted-foreground/80 mt-1">
                        If you have any room or common area maintenance issues, click Raise Complaint.
                      </p>
                    </div>
                  ) : (
                    <div className="grid gap-4">
                      {recentComplaints.items.map((complaint) => (
                        <ComplaintCard key={complaint.id} complaint={complaint} />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              /* Admin Placeholder (since admin pages are not part of this milestone) */
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <div className="group relative rounded-xl border border-border/50 bg-card p-6 shadow-sm">
                  <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <ClipboardList className="h-5 w-5 text-primary" />
                  </div>
                  <h3 className="font-semibold">Admin Panel</h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    View and manage all complaints in your hall.
                  </p>
                  <span className="mt-3 inline-block rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium text-secondary-foreground">
                    Coming soon (Milestone 3)
                  </span>
                </div>
                <div className="group relative rounded-xl border border-border/50 bg-card p-6 shadow-sm">
                  <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <Building2 className="h-5 w-5 text-primary" />
                  </div>
                  <h3 className="font-semibold">Hall Management</h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    View hall information and assigned residents.
                  </p>
                  <span className="mt-3 inline-block rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium text-secondary-foreground">
                    Coming soon
                  </span>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}

