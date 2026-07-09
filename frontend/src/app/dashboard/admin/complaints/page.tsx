"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowLeft, Building2, LogOut, ChevronLeft, ChevronRight, SlidersHorizontal, AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { useAuth } from "@/hooks/use-auth";
import { useHallComplaints } from "@/hooks/use-complaints";
import { AdminComplaintsTable } from "@/components/admin/admin-complaints-table";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";

export default function AdminComplaintQueuePage() {
  const { user, signOut } = useAuth();

  // Filter States
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [sortOption, setSortOption] = useState("newest"); // newest, oldest, priority, status
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // Map sortOption to backend sort parameters
  const getSortParams = (opt: string) => {
    switch (opt) {
      case "oldest":
        return { sort_by: "created_at", sort_order: "asc" };
      case "priority":
        return { sort_by: "priority", sort_order: "desc" };
      case "status":
        return { sort_by: "status", sort_order: "asc" };
      case "newest":
      default:
        return { sort_by: "created_at", sort_order: "desc" };
    }
  };

  const { sort_by, sort_order } = getSortParams(sortOption);

  // Construct query parameters matching backend HallComplaintFilters
  const filters: Record<string, string | number | boolean | null | undefined> = {
    page,
    page_size: pageSize,
    sort_by,
    sort_order,
  };
  if (statusFilter) filters.status = statusFilter;
  if (priorityFilter) filters.priority = priorityFilter;
  if (categoryFilter) filters.category = categoryFilter;
  if (typeFilter) filters.complaint_type = typeFilter;

  const hallId = user?.hall_id || "";
  const hallName = user?.hall_name || "Hostel Hall";

  const {
    data: paginatedData,
    isLoading,
    error,
    isPlaceholderData,
  } = useHallComplaints(hallId, filters);

  const totalItems = paginatedData?.total || 0;
  const totalPages = paginatedData?.pages || 1;
  const complaints = paginatedData?.items || [];

  const handlePrevPage = () => {
    setPage((old) => Math.max(old - 1, 1));
  };

  const handleNextPage = () => {
    if (page < totalPages) {
      setPage((old) => old + 1);
    }
  };

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
          {/* Back to Dashboard */}
          <Link
            href="/dashboard/admin"
            className="inline-flex items-center gap-2 text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Dashboard
          </Link>

          {/* Title & Hall Name */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Complaint Queue</h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Displaying all maintenance requests registered in{" "}
                <span className="font-semibold text-foreground">{hallName}</span>
              </p>
            </div>
          </div>

          {/* Filtering & Sorting Controls Bar */}
          <Card className="border border-border/50 bg-card">
            <CardContent className="p-4 space-y-4">
              <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground border-b border-border/40 pb-2">
                <SlidersHorizontal className="h-3.5 w-3.5" />
                Filter & Sort
              </div>
              <div className="grid gap-3 grid-cols-2 md:grid-cols-5">
                {/* Status Filter */}
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold text-muted-foreground uppercase">Status</label>
                  <select
                    value={statusFilter}
                    onChange={(e) => {
                      setStatusFilter(e.target.value);
                      setPage(1); // Reset to first page on filter change
                    }}
                    className="flex h-9 w-full rounded-md border border-input bg-card px-2.5 py-1 text-xs shadow-xs text-foreground focus-visible:outline-hidden"
                  >
                    <option value="">All Statuses</option>
                    <option value="submitted">Submitted</option>
                    <option value="verified">Verified</option>
                    <option value="scheduled">Scheduled</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                    <option value="visit_failed_room_locked">Failed (Locked)</option>
                    <option value="closed">Closed</option>
                  </select>
                </div>

                {/* Priority Filter */}
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold text-muted-foreground uppercase">Priority</label>
                  <select
                    value={priorityFilter}
                    onChange={(e) => {
                      setPriorityFilter(e.target.value);
                      setPage(1);
                    }}
                    className="flex h-9 w-full rounded-md border border-input bg-card px-2.5 py-1 text-xs shadow-xs text-foreground focus-visible:outline-hidden"
                  >
                    <option value="">All Priorities</option>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>

                {/* Category Filter */}
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold text-muted-foreground uppercase">Category</label>
                  <select
                    value={categoryFilter}
                    onChange={(e) => {
                      setCategoryFilter(e.target.value);
                      setPage(1);
                    }}
                    className="flex h-9 w-full rounded-md border border-input bg-card px-2.5 py-1 text-xs shadow-xs text-foreground focus-visible:outline-hidden"
                  >
                    <option value="">All Categories</option>
                    <option value="electrical">Electrical</option>
                    <option value="plumbing">Plumbing</option>
                    <option value="carpentry">Carpentry</option>
                    <option value="civil">Civil</option>
                    <option value="internet">Internet</option>
                    <option value="cleanliness">Cleanliness</option>
                    <option value="water">Water</option>
                    <option value="furniture">Furniture</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                {/* Type Filter */}
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold text-muted-foreground uppercase">Complaint Type</label>
                  <select
                    value={typeFilter}
                    onChange={(e) => {
                      setTypeFilter(e.target.value);
                      setPage(1);
                    }}
                    className="flex h-9 w-full rounded-md border border-input bg-card px-2.5 py-1 text-xs shadow-xs text-foreground focus-visible:outline-hidden"
                  >
                    <option value="">All Types</option>
                    <option value="personal">Personal</option>
                    <option value="common_area">Common Area</option>
                  </select>
                </div>

                {/* Sorting */}
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold text-muted-foreground uppercase">Sort By</label>
                  <select
                    value={sortOption}
                    onChange={(e) => {
                      setSortOption(e.target.value);
                      setPage(1);
                    }}
                    className="flex h-9 w-full rounded-md border border-input bg-card px-2.5 py-1 text-xs shadow-xs text-foreground focus-visible:outline-hidden"
                  >
                    <option value="newest">Newest First</option>
                    <option value="oldest">Oldest First</option>
                    <option value="priority">Priority (High-Low)</option>
                    <option value="status">Status (A-Z)</option>
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Loader, Error, Table rendering */}
          {isLoading ? (
            <LoadingSkeleton variant="list" />
          ) : error ? (
            <Card className="border border-destructive/20 bg-destructive/5">
              <CardContent className="p-8 text-center flex flex-col items-center gap-2">
                <AlertTriangle className="h-8 w-8 text-destructive" />
                <p className="text-sm font-semibold text-destructive">Failed to fetch complaints</p>
                <p className="text-xs text-muted-foreground">Please try reloading the page.</p>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Complaints Table Grid */}
              <AdminComplaintsTable complaints={complaints} />

              {/* Backend Pagination Bar */}
              {totalPages > 1 && (
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-border/40 pt-4">
                  <span className="text-xs text-muted-foreground">
                    Showing page <span className="font-semibold text-foreground">{page}</span> of{" "}
                    <span className="font-semibold text-foreground">{totalPages}</span> (
                    <span className="font-semibold text-foreground">{totalItems}</span> total complaints)
                  </span>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handlePrevPage}
                      disabled={page === 1 || isPlaceholderData}
                      className="h-8 gap-1 text-xs"
                    >
                      <ChevronLeft className="h-4 w-4" />
                      Prev
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleNextPage}
                      disabled={page >= totalPages || isPlaceholderData}
                      className="h-8 gap-1 text-xs"
                    >
                      Next
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
