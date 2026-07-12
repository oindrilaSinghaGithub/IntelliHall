"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Building2,
  CalendarDays,
  Download,
  Loader2,
  LogOut,
  SlidersHorizontal,
} from "lucide-react";

import { AuthGuard } from "@/components/shared/auth-guard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/use-auth";
import { useSchedule, useExportSchedule } from "@/hooks/use-schedule";
import { ScheduleTable } from "@/components/admin/schedule-table";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";
import type { ScheduleFilters } from "@/services/schedule";

const MAINTENANCE_TYPES = [
  { value: "electrician", label: "Electrician" },
  { value: "plumber", label: "Plumber" },
  { value: "carpenter", label: "Carpenter" },
  { value: "mason", label: "Mason" },
  { value: "cleaning_staff", label: "Cleaning Staff" },
  { value: "civil", label: "Civil" },
  { value: "network", label: "Network" },
  { value: "housekeeping", label: "Housekeeping" },
  { value: "other", label: "Other" },
];

const CATEGORIES = [
  { value: "electrical", label: "Electrical" },
  { value: "plumbing", label: "Plumbing" },
  { value: "carpentry", label: "Carpentry" },
  { value: "civil", label: "Civil" },
  { value: "internet", label: "Internet" },
  { value: "cleanliness", label: "Cleanliness" },
  { value: "water", label: "Water" },
  { value: "furniture", label: "Furniture" },
  { value: "other", label: "Other" },
];

export default function AdminSchedulePage() {
  const { user, signOut } = useAuth();
  const hallId = user?.hall_id || "";

  const [scheduledDate, setScheduledDate] = useState("");
  const [workerName, setWorkerName] = useState("");
  const [workerType, setWorkerType] = useState("");
  const [category, setCategory] = useState("");

  const filters: ScheduleFilters = {
    scheduled_date: scheduledDate || null,
    worker_name: workerName || null,
    worker_type: workerType || null,
    category: category || null,
  };

  const { data: scheduleItems, isLoading, error } = useSchedule(hallId, filters);
  const exportMutation = useExportSchedule(hallId);

  const handleExport = () => {
    exportMutation.mutate(filters);
  };

  return (
    <AuthGuard>
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

        <main className="flex-1">
          <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 space-y-6">
            {/* Back */}
            <Link
              href="/dashboard/admin"
              className="inline-flex items-center gap-2 text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Back to Dashboard
            </Link>

            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                  <CalendarDays className="h-6 w-6 text-primary" />
                  Work Schedule
                </h1>
                <p className="mt-1 text-sm text-muted-foreground">
                  All scheduled and in-progress maintenance visits for{" "}
                  <span className="font-semibold text-foreground">{user?.hall_name || "your hall"}</span>
                </p>
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={handleExport}
                disabled={exportMutation.isPending || !scheduleItems?.length}
                className="gap-1.5 text-xs self-start sm:self-auto"
              >
                {exportMutation.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Download className="h-3.5 w-3.5" />
                )}
                Export PDF
              </Button>
            </div>

            {/* Filter bar */}
            <Card className="border border-border/50 bg-card">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground border-b border-border/40 pb-2 mb-3">
                  <SlidersHorizontal className="h-3.5 w-3.5" />
                  Filters
                </div>
                <div className="grid gap-3 grid-cols-2 md:grid-cols-4">
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-muted-foreground uppercase">Visit Date</label>
                    <input
                      type="date"
                      value={scheduledDate}
                      onChange={(e) => setScheduledDate(e.target.value)}
                      className="flex h-9 w-full rounded-md border border-input bg-card px-3 py-1 text-xs shadow-xs text-foreground focus-visible:outline-hidden"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-muted-foreground uppercase">Worker Name</label>
                    <Input
                      placeholder="Search worker…"
                      value={workerName}
                      onChange={(e) => setWorkerName(e.target.value)}
                      className="h-9 text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-muted-foreground uppercase">Worker Type</label>
                    <select
                      value={workerType}
                      onChange={(e) => setWorkerType(e.target.value)}
                      className="flex h-9 w-full rounded-md border border-input bg-card px-2.5 py-1 text-xs shadow-xs text-foreground focus-visible:outline-hidden"
                    >
                      <option value="">All Types</option>
                      {MAINTENANCE_TYPES.map((t) => (
                        <option key={t.value} value={t.value}>{t.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-muted-foreground uppercase">Category</label>
                    <select
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                      className="flex h-9 w-full rounded-md border border-input bg-card px-2.5 py-1 text-xs shadow-xs text-foreground focus-visible:outline-hidden"
                    >
                      <option value="">All Categories</option>
                      {CATEGORIES.map((c) => (
                        <option key={c.value} value={c.value}>{c.label}</option>
                      ))}
                    </select>
                  </div>
                </div>
                {(scheduledDate || workerName || workerType || category) && (
                  <div className="mt-3">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-xs h-7 text-muted-foreground"
                      onClick={() => {
                        setScheduledDate("");
                        setWorkerName("");
                        setWorkerType("");
                        setCategory("");
                      }}
                    >
                      Clear filters
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Content */}
            {isLoading ? (
              <LoadingSkeleton variant="list" count={4} />
            ) : error ? (
              <Card className="border border-destructive/20 bg-destructive/5">
                <CardContent className="p-8 text-center text-destructive">
                  <p className="font-semibold">Failed to load schedule</p>
                  <p className="text-sm mt-1 opacity-80">
                    {error instanceof Error ? error.message : "Please try again."}
                  </p>
                </CardContent>
              </Card>
            ) : (
              <>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>
                    <span className="font-semibold text-foreground">{scheduleItems?.length ?? 0}</span> item(s) found
                  </span>
                </div>
                <ScheduleTable items={scheduleItems ?? []} />
              </>
            )}
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
