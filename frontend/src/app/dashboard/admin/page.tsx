"use client";

import Link from "next/link";
import {
  Building2,
  LogOut,
  LayoutDashboard,
  ClipboardList,
  Clock,
  Wrench,
  CheckCircle2,
  BarChart3,
  ListTodo,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/use-auth";
import { useHallComplaints } from "@/hooks/use-complaints";
import { ComplaintStatusBadge } from "@/components/shared/complaint-status-badge";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";

export default function AdminDashboardPage() {
  const { user, signOut } = useAuth();

  const hallId = user?.hall_id || "";
  const { data: paginatedData, isLoading: isComplaintsLoading } = useHallComplaints(hallId, {
    page: 1,
    page_size: 100,
  });

  const complaints = paginatedData?.items || [];
  const totalCount = paginatedData?.total || 0;
  const pendingCount = complaints.filter(
    (c) =>
      c.status === "submitted" ||
      c.status === "verified" ||
      c.status === "scheduled"
  ).length;
  const inProgressCount = complaints.filter((c) => c.status === "in_progress").length;
  const completedCount = complaints.filter(
    (c) => c.status === "completed" || c.status === "closed"
  ).length;

  const recentComplaints = complaints.slice(0, 3);

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* Top nav */}
      <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link href="/dashboard/admin" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
              <Building2 className="h-4 w-4 text-primary" />
            </div>
            <span className="text-sm font-semibold tracking-tight">IntelliHall Admin</span>
          </Link>

          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium">{user?.name}</p>
              <p className="text-xs text-muted-foreground">{user?.email}</p>
            </div>
            <Badge variant="default">Hall Admin</Badge>
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
        <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 space-y-6">
          {/* Welcome banner and Hall info */}
          <div className="grid gap-6 md:grid-cols-3">
            {/* Welcome Message Banner */}
            <div className="md:col-span-2 rounded-2xl border border-border/50 bg-card p-8 shadow-xs flex items-start gap-4">
              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-primary/10">
                <LayoutDashboard className="h-7 w-7 text-primary" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">
                  Welcome back, {user?.name?.split(" ")[0]}! 🏛️
                </h1>
                <p className="mt-1.5 text-sm text-muted-foreground">
                  You are logged in as a Hall Administrator. You can monitor hostel maintenance requests, assign technicians, and coordinate workflows.
                </p>
                <div className="mt-4 flex gap-3">
                  <Link href="/dashboard/admin/complaints">
                    <Button size="sm" className="gap-1.5 text-xs font-semibold">
                      <ClipboardList className="h-3.5 w-3.5" />
                      View Complaint Queue
                    </Button>
                  </Link>
                </div>
              </div>
            </div>

            {/* Hall Information Card */}
            <Card className="border border-border/50 bg-card">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-bold flex items-center gap-2">
                  <Building2 className="h-4 w-4 text-primary" />
                  Hall Information
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="p-3 rounded-lg bg-muted/40 border border-border/40 text-center">
                  <p className="text-xs font-semibold text-foreground">
                    {user?.hall_name || "Hall information unavailable"}
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Statistics Grid */}
          <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
            {[
              {
                title: "Total Complaints",
                value: isComplaintsLoading ? "..." : String(totalCount),
                desc: "All registered complaints",
                icon: ClipboardList,
                color: "text-blue-500 bg-blue-500/10",
              },
              {
                title: "Pending Complaints",
                value: isComplaintsLoading ? "..." : String(pendingCount),
                desc: "Awaiting verification",
                icon: Clock,
                color: "text-amber-500 bg-amber-500/10",
              },
              {
                title: "In Progress",
                value: isComplaintsLoading ? "..." : String(inProgressCount),
                desc: "Currently being fixed",
                icon: Wrench,
                color: "text-purple-500 bg-purple-500/10",
              },
              {
                title: "Completed",
                value: isComplaintsLoading ? "..." : String(completedCount),
                desc: "Resolved issues",
                icon: CheckCircle2,
                color: "text-emerald-500 bg-emerald-500/10",
              },
            ].map((stat, idx) => (
              <Card key={idx} className="border border-border/50 bg-card">
                <CardContent className="p-6 flex items-start justify-between">
                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-muted-foreground tracking-wider uppercase">
                      {stat.title}
                    </p>
                    <p className="text-2xl font-bold tracking-tight">{stat.value}</p>
                    <p className="text-[10px] text-muted-foreground">{stat.desc}</p>
                  </div>
                  <div className={`p-2.5 rounded-lg ${stat.color}`}>
                    <stat.icon className="h-5 w-5" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Placeholder Sections */}
          <div className="grid gap-6 md:grid-cols-3">
            {/* Recent Complaints */}
            <div className="md:col-span-2 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold tracking-tight flex items-center gap-2">
                  <ListTodo className="h-5 w-5 text-primary" />
                  Recent Complaints
                </h2>
                {recentComplaints.length > 0 && (
                  <Link href="/dashboard/admin/complaints" className="text-xs font-semibold text-primary hover:underline">
                    View full queue →
                  </Link>
                )}
              </div>

              {isComplaintsLoading ? (
                <LoadingSkeleton variant="list" count={3} />
              ) : recentComplaints.length === 0 ? (
                <Card className="border border-dashed border-border bg-card/60">
                  <CardContent className="p-12 text-center flex flex-col items-center justify-center min-h-[220px]">
                    <p className="text-sm font-medium text-muted-foreground">
                      No complaints registered in this hall yet.
                    </p>
                    <Link href="/dashboard/admin/complaints" className="mt-3">
                      <Button variant="outline" size="sm" className="text-xs">
                        Go to Complaint Queue
                      </Button>
                    </Link>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid gap-4">
                  {recentComplaints.map((c) => {
                    const locationText =
                      c.complaint_type === "personal"
                        ? `Room ${c.room_number || "N/A"}`
                        : [c.block, c.floor, c.common_area]
                            .filter(Boolean)
                            .join(", ") || "Common Area";
                    return (
                      <Link href={`/dashboard/admin/complaints/${c.id}`} key={c.id} className="block group">
                        <Card className="overflow-hidden border border-border/50 bg-card transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-md">
                          <CardContent className="p-4 flex items-center justify-between gap-4">
                            <div className="space-y-1.5 flex-1">
                              <div className="flex items-center gap-2 text-[10px]">
                                <span className="font-semibold px-2 py-0.5 rounded bg-muted text-muted-foreground uppercase">
                                  {c.category}
                                </span>
                                <span className="text-muted-foreground">
                                  {locationText}
                                </span>
                              </div>
                              <h4 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors line-clamp-1">
                                {c.title}
                              </h4>
                              <p className="text-[10px] text-muted-foreground">
                                By {c.student_name || "Unknown"} on {new Date(c.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                              </p>
                            </div>
                            <ComplaintStatusBadge status={c.status} />
                          </CardContent>
                        </Card>
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Analytics Placeholder */}
            <div className="space-y-4">
              <h2 className="text-lg font-bold tracking-tight flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-primary" />
                Analytics Overview
              </h2>
              <Card className="border border-dashed border-border bg-card/60">
                <CardContent className="p-12 text-center flex flex-col items-center justify-center min-h-[220px]">
                  <p className="text-sm font-medium text-muted-foreground">
                    This section will be implemented in Milestone 2.
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
