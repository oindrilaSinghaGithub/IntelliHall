"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, Building2, ClipboardList, LogOut, Plus } from "lucide-react";

import { AuthGuard } from "@/components/shared/auth-guard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/use-auth";
import { useComplaints } from "@/hooks/use-complaints";
import { ComplaintCard } from "@/components/shared/complaint-card";
import { EmptyState } from "@/components/shared/empty-state";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";

export default function ComplaintsListPage() {
  const { user, signOut } = useAuth();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [priorityFilter, setPriorityFilter] = useState<string>("");

  // Prepare query params
  const filters: Record<string, string | number> = {
    page,
    page_size: 10,
    sort_by: "created_at",
    sort_order: "desc", // Newest first
  };

  if (statusFilter) filters.status = statusFilter;
  if (priorityFilter) filters.priority = priorityFilter;

  const { data, isLoading, error, isPlaceholderData } = useComplaints(filters);

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
          <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
            {/* Header section */}
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-8">
              <div className="space-y-1">
                <Link
                  href="/dashboard"
                  className="inline-flex items-center text-xs font-medium text-muted-foreground hover:text-primary gap-1 mb-2 transition-colors"
                >
                  <ArrowLeft className="h-3 w-3" />
                  Back to Dashboard
                </Link>
                <h1 className="text-2xl font-bold flex items-center gap-2">
                  <ClipboardList className="h-6 w-6 text-primary" />
                  My Complaints
                </h1>
                <p className="text-sm text-muted-foreground">
                  Track, view details, and manage complaints raised by you.
                </p>
              </div>
              
              <Button asChild className="sm:self-end gap-1.5 shadow-sm">
                <Link href="/dashboard/complaints/new">
                  <Plus className="h-4 w-4" />
                  New Complaint
                </Link>
              </Button>
            </div>

            {/* Filter controls */}
            <div className="flex flex-wrap gap-4 items-center justify-between mb-6 p-4 rounded-xl border border-border bg-card/60">
              <div className="flex flex-wrap gap-3 items-center">
                <div className="flex flex-col gap-1">
                  <label htmlFor="filter-status" className="text-xs font-semibold text-muted-foreground">
                    Status
                  </label>
                  <select
                    id="filter-status"
                    value={statusFilter}
                    onChange={(e) => {
                      setStatusFilter(e.target.value);
                      setPage(1);
                    }}
                    className="h-8 rounded-md border border-input bg-card px-2.5 py-1 text-xs shadow-xs focus-visible:ring-1 focus-visible:ring-ring text-foreground"
                  >
                    <option value="">All Statuses</option>
                    <option value="submitted">Submitted</option>
                    <option value="verified">Verified</option>
                    <option value="scheduled">Scheduled</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                    <option value="waiting_student_confirmation">Awaiting Confirmation</option>
                    <option value="closed">Closed</option>
                    <option value="visit_failed_room_locked">Visit Failed (Locked)</option>
                  </select>
                </div>

                <div className="flex flex-col gap-1">
                  <label htmlFor="filter-priority" className="text-xs font-semibold text-muted-foreground">
                    Priority
                  </label>
                  <select
                    id="filter-priority"
                    value={priorityFilter}
                    onChange={(e) => {
                      setPriorityFilter(e.target.value);
                      setPage(1);
                    }}
                    className="h-8 rounded-md border border-input bg-card px-2.5 py-1 text-xs shadow-xs focus-visible:ring-1 focus-visible:ring-ring text-foreground"
                  >
                    <option value="">All Priorities</option>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
              </div>

              <div className="text-xs text-muted-foreground">
                Total Complaints: <span className="font-semibold text-foreground">{data?.total || 0}</span>
              </div>
            </div>

            {/* Content states */}
            {isLoading ? (
              <LoadingSkeleton variant="list" count={4} />
            ) : error ? (
              <div className="rounded-2xl border border-destructive/20 bg-destructive/5 p-8 text-center text-destructive">
                <p className="font-semibold">Failed to load complaints</p>
                <p className="text-sm mt-1 opacity-80">
                  {error instanceof Error ? error.message : "Please check your network and try again."}
                </p>
                <Button onClick={() => setPage(1)} variant="outline" className="mt-4 border-destructive/30 hover:bg-destructive/10">
                  Retry
                </Button>
              </div>
            ) : !data || data.items.length === 0 ? (
              <EmptyState
                title={statusFilter || priorityFilter ? "No matching complaints" : "No complaints raised"}
                description={
                  statusFilter || priorityFilter
                    ? "Try clearing or changing your filters to see results."
                    : "You haven't raised any maintenance complaints yet."
                }
                actionLabel={statusFilter || priorityFilter ? "" : "Raise a Complaint"}
                actionHref={statusFilter || priorityFilter ? "" : "/dashboard/complaints/new"}
              />
            ) : (
              <div className="space-y-6">
                <div className="grid gap-4">
                  {data.items.map((complaint) => (
                    <ComplaintCard key={complaint.id} complaint={complaint} />
                  ))}
                </div>

                {/* Pagination */}
                {data.pages > 1 && (
                  <div className="flex items-center justify-between border-t border-border/40 pt-6">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((old) => Math.max(old - 1, 1))}
                      disabled={page === 1}
                    >
                      Previous
                    </Button>
                    <span className="text-xs text-muted-foreground">
                      Page <span className="font-semibold text-foreground">{page}</span> of{" "}
                      <span className="font-semibold text-foreground">{data.pages}</span>
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((old) => (page < data.pages ? old + 1 : old))}
                      disabled={page >= data.pages || isPlaceholderData}
                    >
                      Next
                    </Button>
                  </div>
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
