"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Building2, LogOut, ClipboardList, LayoutDashboard, Plus, ArrowRight, CheckCircle2, Clock, XCircle, User } from "lucide-react";
import Link from "next/link";

import { AuthGuard } from "@/components/shared/auth-guard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/use-auth";
import { useComplaints } from "@/hooks/use-complaints";
import { ComplaintCard } from "@/components/shared/complaint-card";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { NotificationBell } from "@/components/shared/notification-bell";

export default function DashboardPage() {
  const router = useRouter();
  const { user, signOut } = useAuth();

  // Redirect admin users to their dedicated dashboard
  useEffect(() => {
    if (user && user.role === "hall_admin") {
      router.replace("/dashboard/admin");
    }
  }, [user, router]);

  // Fetch complaints for student (larger page size to compute stats client-side)
  const isStudent = user?.role === "student";
  const { data: complaintsData, isLoading: isComplaintsLoading } = useComplaints(
    isStudent
      ? {
          page: 1,
          page_size: 100,
          sort_by: "created_at",
          sort_order: "desc",
        }
      : { page: 1, page_size: 1 } // dummy/not used for admins
  );

  const allComplaints = complaintsData?.items || [];
  const displayedRecentComplaints = allComplaints.slice(0, 3);

  // Compute student stats
  const stats = {
    total: allComplaints.length,
    submitted: allComplaints.filter((c) =>
      ["submitted", "verified", "scheduled", "reopened"].includes(c.status)
    ).length,
    inProgress: allComplaints.filter((c) =>
      ["in_progress", "visit_failed_room_locked"].includes(c.status)
    ).length,
    completed: allComplaints.filter((c) =>
      ["completed", "waiting_student_confirmation"].includes(c.status)
    ).length,
    closed: allComplaints.filter((c) => c.status === "closed").length,
  };

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
              <NotificationBell />
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

            {/* ── Verification status banner (students only) ─────────────── */}
            {isStudent && (() => {
              const status = user?.hall_verification_status;
              if (status === "approved") return null;
              if (status === "pending") return (
                <div className="mb-8 flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-5 py-4 dark:border-amber-800/40 dark:bg-amber-900/20">
                  <Clock className="mt-0.5 h-5 w-5 shrink-0 text-amber-500" />
                  <div>
                    <p className="text-sm font-semibold text-amber-700 dark:text-amber-400">
                      🟡 Hall Affiliation Pending Verification
                    </p>
                    <p className="mt-0.5 text-xs text-amber-600 dark:text-amber-500">
                      Your hall affiliation is awaiting verification by the Hall Office.
                      Complaint submission will be enabled after approval.
                    </p>
                  </div>
                </div>
              );
              if (status === "rejected") return (
                <div className="mb-8 flex items-start gap-3 rounded-xl border border-destructive/30 bg-destructive/5 px-5 py-4">
                  <XCircle className="mt-0.5 h-5 w-5 shrink-0 text-destructive" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-destructive">
                      🔴 Hall Verification Rejected
                    </p>
                    {user?.hall_rejection_reason && (
                      <p className="mt-0.5 text-xs text-destructive/80">
                        Reason: {user.hall_rejection_reason}
                      </p>
                    )}
                    <p className="mt-1.5 text-xs text-muted-foreground">
                      Please update your hall information from your{" "}
                      <Link href="/profile" className="underline font-medium text-primary hover:text-primary/80">
                        profile
                      </Link>
                      {" "}to re-submit for verification.
                    </p>
                  </div>
                </div>
              );
              return null;
            })()}

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
                      {user?.hall_verification_status === "approved" || user?.role !== "student" ? (
                        <Button asChild className="w-full gap-1.5 shadow-xs">
                          <Link href="/dashboard/complaints/new">
                            <Plus className="h-4 w-4" />
                            Raise Complaint
                          </Link>
                        </Button>
                      ) : (
                        <Button className="w-full gap-1.5 shadow-xs" disabled title="Complaint submission is locked until your hall affiliation is verified.">
                          <Plus className="h-4 w-4" />
                          Raise Complaint
                        </Button>
                      )}
                      <Button asChild variant="outline" className="w-full gap-1.5">
                        <Link href="/dashboard/complaints">
                          View My Complaints
                        </Link>
                      </Button>
                    </CardContent>
                  </Card>

                  {/* My Complaint Summary Card */}
                  <Card className="border border-border/50 bg-card">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-lg font-bold flex items-center gap-2">
                        <ClipboardList className="h-5 w-5 text-primary" />
                        My Complaint Summary
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {allComplaints.length === 0 ? (
                        <p className="text-xs text-muted-foreground text-center py-4">
                          No complaints submitted yet.
                        </p>
                      ) : (
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="col-span-2 flex items-center justify-between p-2 rounded-lg bg-primary/5 border border-primary/10">
                            <span className="font-semibold text-foreground">Total Complaints</span>
                            <span className="font-bold text-sm text-primary">{stats.total}</span>
                          </div>
                          <div className="flex items-center justify-between p-2 rounded-lg bg-blue-500/5 border border-blue-500/10">
                            <span className="text-muted-foreground">Submitted</span>
                            <Badge variant="outline" className="bg-blue-500/10 text-blue-500 hover:bg-blue-500/20 font-bold border-none">{stats.submitted}</Badge>
                          </div>
                          <div className="flex items-center justify-between p-2 rounded-lg bg-amber-500/5 border border-amber-500/10">
                            <span className="text-muted-foreground">In Progress</span>
                            <Badge variant="outline" className="bg-amber-500/10 text-amber-500 hover:bg-amber-500/20 font-bold border-none">{stats.inProgress}</Badge>
                          </div>
                          <div className="flex items-center justify-between p-2 rounded-lg bg-emerald-500/5 border border-emerald-500/10">
                            <span className="text-muted-foreground">Completed</span>
                            <Badge variant="outline" className="bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 font-bold border-none">{stats.completed}</Badge>
                          </div>
                          <div className="flex items-center justify-between p-2 rounded-lg bg-slate-500/5 border border-slate-500/10">
                            <span className="text-muted-foreground">Closed</span>
                            <Badge variant="outline" className="bg-slate-500/10 text-slate-400 hover:bg-slate-500/20 font-bold border-none">{stats.closed}</Badge>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>

                {/* Recent Complaints Column */}
                <div className="md:col-span-2 space-y-4">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-bold tracking-tight">Recent Complaints</h2>
                    {allComplaints.length > 0 && (
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
                  ) : allComplaints.length === 0 ? (
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
                      {displayedRecentComplaints.map((complaint) => (
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

